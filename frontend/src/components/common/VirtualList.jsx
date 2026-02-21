
import React from 'react';
import { FixedSizeList as List } from 'react-window';
import AutoSizer from 'react-virtualized-auto-sizer';

/**
 * A generic virtualized list component for handling large datasets efficiently.
 * 
 * @param {Array} items - The data array to render.
 * @param {number} rowHeight - Height of each row in pixels.
 * @param {Function} rowRenderer - Function that returns JSX for a row. Receives { index, item, style }.
 * @param {string} className - Optional CSS class for the container.
 */
const VirtualList = ({ items, rowHeight = 50, rowRenderer, className }) => {
    if (!items || items.length === 0) {
        return <div className="no-data">No data available</div>;
    }

    return (
        <div className={`virtual-list-container ${className || ''}`} style={{ flex: 1, minHeight: '400px', height: '100%', width: '100%' }}>
            <AutoSizer>
                {({ height, width }) => (
                    <List
                        height={height}
                        itemCount={items.length}
                        itemSize={rowHeight}
                        width={width}
                        className="virtual-list"
                    >
                        {({ index, style }) => (
                            <div style={style} className="virtual-row">
                                {rowRenderer({ index, item: items[index] })}
                            </div>
                        )}
                    </List>
                )}
            </AutoSizer>
        </div>
    );
};

export default VirtualList;
