import React, { createContext, useContext, useState, useEffect } from 'react';
import { branchesAPI } from '../utils/api';
import { isAuthenticated, getUser } from '../utils/auth';

const BranchContext = createContext();

export const useBranch = () => {
    const context = useContext(BranchContext);
    if (!context) {
        throw new Error('useBranch must be used within a BranchProvider');
    }
    return context;
};

export const BranchProvider = ({ children }) => {
    const [branches, setBranches] = useState([]);
    const [currentBranch, setCurrentBranch] = useState(null);
    const [loading, setLoading] = useState(true);

    const fetchBranches = async () => {
        if (!isAuthenticated()) {
            setLoading(false);
            return;
        }

        try {
            const res = await branchesAPI.list();
            setBranches(res.data);

            const user = getUser();
            const isAdmin = user?.role === 'admin' || user?.role === 'system_admin' || user?.permissions?.includes('*');

            // Selection Logic:
            // 1. If user is Admin/Manager and has no saved preference (or it's 'all'), pick Default Branch
            // 2. If user has saved preference, use it
            // 3. If no preference, pick Default Branch

            const savedBranchId = localStorage.getItem('current_branch_id');
            let branchToSet = null;

            if (isAdmin) {
                // Admin/Superuser: Default to ALL (null) unless specific branch is saved and valid
                if (savedBranchId && savedBranchId !== 'all') {
                    branchToSet = res.data.find(b => b.id === parseInt(savedBranchId)) || null;
                } else {
                    branchToSet = null; // 'all' or no preference -> Show All
                }
            } else {
                // Regular User: Must always have a branch selected (first allowed one if none saved)
                if (savedBranchId && savedBranchId !== 'all') {
                    branchToSet = res.data.find(b => b.id === parseInt(savedBranchId)) || res.data[0];
                } else {
                    branchToSet = res.data.length > 0 ? res.data[0] : null;
                }
            }

            setCurrentBranch(branchToSet);
            if (branchToSet) {
                localStorage.setItem('current_branch_id', branchToSet.id);
            }

        } catch (error) {
            console.error('Error fetching branches for context:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchBranches();
    }, []);

    const setBranch = (branch) => {
        setCurrentBranch(branch);
        if (branch) {
            localStorage.setItem('current_branch_id', branch.id);
        } else {
            localStorage.setItem('current_branch_id', 'all');
        }
    };

    return (
        <BranchContext.Provider value={{ branches, currentBranch, setBranch, loading, refreshBranches: fetchBranches }}>
            {children}
        </BranchContext.Provider>
    );
};
