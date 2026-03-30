"""Projects, contracts, and CRM entities."""

from .. import (
    Contract,
    ContractAmendment,
    ContractItem,
    CrmContact,
    CrmCustomerSegment,
    CrmCustomerSegmentMember,
    CrmKnowledgeBase,
    CrmLeadScore,
    CrmLeadScoringRule,
    CrmSalesForecast,
    CustomerGroup,
    Project,
    ProjectBudget,
    ProjectChangeOrder,
    ProjectDocument,
    ProjectExpense,
    ProjectRevenue,
    ProjectTask,
)
from ..domain_models.projects_dependencies import TaskDependency
from ..domain_models.projects_execution import OpportunityActivity, ProjectRisk, ProjectTimesheet

__all__ = [
    "Project",
    "ProjectTask",
    "ProjectBudget",
    "ProjectExpense",
    "ProjectRevenue",
    "ProjectDocument",
    "ProjectChangeOrder",
    "ProjectRisk",
    "ProjectTimesheet",
    "TaskDependency",
    "Contract",
    "ContractItem",
    "ContractAmendment",
    "CrmLeadScoringRule",
    "CrmLeadScore",
    "CrmCustomerSegment",
    "CrmCustomerSegmentMember",
    "CrmSalesForecast",
    "CrmContact",
    "CrmKnowledgeBase",
    "OpportunityActivity",
    "CustomerGroup",
]
