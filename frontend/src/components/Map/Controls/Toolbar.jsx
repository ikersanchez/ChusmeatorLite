import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import './Toolbar.css';
import HelpModal from './HelpModal';
import FilterMenu from './FilterMenu';

const Toolbar = ({ mode, onModeChange, filters, onFiltersChange, availableYears }) => {
    const [showHelp, setShowHelp] = React.useState(false);
    const [showFilters, setShowFilters] = React.useState(false);
    const toolbarRef = useRef(null);

    const modes = [
        { id: 'VIEW', label: 'View', icon: '👁️', description: 'Navigate the map' },
        { id: 'PIN', label: 'Pin', icon: '📍', description: 'Click to add a pin' },
        { id: 'AREA', label: 'Area', icon: '🗺️', description: 'Draw an area on the map' },
    ];

    useEffect(() => {
        if (toolbarRef.current) {
            // Leaflet utility to stop all event propagation through the element
            L.DomEvent.disableClickPropagation(toolbarRef.current);
            L.DomEvent.disableScrollPropagation(toolbarRef.current);
        }
    }, []);

    const handleModeClick = (e, newMode) => {
        e.stopPropagation();
        onModeChange(newMode);
    };

    const handleHelpClick = (e) => {
        e.stopPropagation();
        setShowHelp(true);
    };

    const handleFilterClick = (e) => {
        e.stopPropagation();
        setShowFilters(!showFilters);
    };

    // Generic handler to stop events at the container level
    const stopPropagation = (e) => {
        e.stopPropagation();
    };

    return (
        <>
            <div
                className="toolbar"
                ref={toolbarRef}
                onMouseDown={stopPropagation}
                onPointerDown={stopPropagation}
                onTouchStart={stopPropagation}
                onClick={stopPropagation}
            >
                <div className="toolbar-buttons">
                    {modes.map((m) => (
                        <button
                            key={m.id}
                            className={`toolbar-btn ${mode === m.id ? 'active' : ''}`}
                            onClick={(e) => handleModeClick(e, m.id)}
                            title={m.description}
                        >
                            <span className="toolbar-icon">{m.icon}</span>
                            <span className="toolbar-label">{m.label}</span>
                        </button>
                    ))}
                    <button
                        className={`toolbar-btn ${showFilters ? 'active' : ''}`}
                        onClick={handleFilterClick}
                        title="Filters & Tools"
                    >
                        <span className="toolbar-icon">🔧</span>
                        <span className="toolbar-label">Tools</span>
                    </button>
                </div>
                <button
                    className="toolbar-help-btn"
                    onClick={handleHelpClick}
                    title="Help & Info"
                >
                    ?
                </button>
            </div>
            {showHelp && <HelpModal onClose={() => setShowHelp(false)} />}
            {showFilters && (
                <FilterMenu 
                    filters={filters} 
                    onFiltersChange={onFiltersChange} 
                    onClose={() => setShowFilters(false)} 
                    availableYears={availableYears}
                />
            )}
        </>
    );
};

export default Toolbar;
