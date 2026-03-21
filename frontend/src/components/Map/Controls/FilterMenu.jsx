import React, { useState, useEffect, useRef } from 'react';
import L from 'leaflet';
import './FilterMenu.css';

const FilterMenu = ({ filters, onFiltersChange, onClose, availableYears }) => {
    const [localFilters, setLocalFilters] = useState(JSON.parse(JSON.stringify(filters)));
    const overlayRef = useRef(null);

    useEffect(() => {
        if (overlayRef.current) {
            L.DomEvent.disableClickPropagation(overlayRef.current);
            L.DomEvent.disableScrollPropagation(overlayRef.current);
        }
    }, []);

    const handleColorChange = (type, color) => {
        setLocalFilters(prev => ({
            ...prev,
            [type]: { ...prev[type], color }
        }));
    };

    const handleDateChange = (type, field, value) => {
        setLocalFilters(prev => ({
            ...prev,
            [type]: { ...prev[type], [field]: value }
        }));
    };

    const handleReset = () => {
        const resetFilters = {
            pins: { color: 'all', startMonth: '', startYear: '', endMonth: '', endYear: '' },
            areas: { color: 'all', startMonth: '', startYear: '', endMonth: '', endYear: '' }
        };
        setLocalFilters(resetFilters);
    };

    const handleApply = () => {
        onFiltersChange(localFilters);
        onClose();
    };

    const months = [
        { value: '', label: 'Month' },
        { value: '01', label: '01' },
        { value: '02', label: '02' },
        { value: '03', label: '03' },
        { value: '04', label: '04' },
        { value: '05', label: '05' },
        { value: '06', label: '06' },
        { value: '07', label: '07' },
        { value: '08', label: '08' },
        { value: '09', label: '09' },
        { value: '10', label: '10' },
        { value: '11', label: '11' },
        { value: '12', label: '12' },
    ];

    const yearOptions = [
        { value: '', label: 'Year' },
        ...(availableYears || []).map(y => ({ value: y, label: y }))
    ];

    const FilterSection = ({ type, title }) => (
        <div className="filter-section">
            <h3>{title}</h3>
            <div className="filter-group">
                <div className="filter-row">
                    <label>Color</label>
                    <div className="color-options">
                        {['all', 'none', 'blue', 'green', 'red'].map(c => (
                            <div
                                key={c}
                                className={`color-option color-${c} ${localFilters[type].color === c ? 'active' : ''}`}
                                onClick={() => handleColorChange(type, c)}
                                title={c.toUpperCase()}
                            >
                                {c === 'all' && 'ALL'}
                                {c === 'none' && 'NONE'}
                            </div>
                        ))}
                    </div>
                </div>

                <div className="filter-row">
                    <label>Date Range (Start → End)</label>
                    <div className="date-range-inputs">
                        <div className="date-input-group">
                            <select
                                className="date-input"
                                value={localFilters[type].startMonth}
                                onChange={(e) => handleDateChange(type, 'startMonth', e.target.value)}
                            >
                                {months.map(m => <option key={m.value} value={m.value}>{m.label}</option>)}
                            </select>
                            <select
                                className="date-input"
                                value={localFilters[type].startYear}
                                onChange={(e) => handleDateChange(type, 'startYear', e.target.value)}
                            >
                                {yearOptions.map(y => <option key={y.value} value={y.value}>{y.label}</option>)}
                            </select>
                        </div>
                        <span className="date-separator">→</span>
                        <div className="date-input-group">
                            <select
                                className="date-input"
                                value={localFilters[type].endMonth}
                                onChange={(e) => handleDateChange(type, 'endMonth', e.target.value)}
                            >
                                {months.map(m => <option key={m.value} value={m.value}>{m.label}</option>)}
                            </select>
                            <select
                                className="date-input"
                                value={localFilters[type].endYear}
                                onChange={(e) => handleDateChange(type, 'endYear', e.target.value)}
                            >
                                {yearOptions.map(y => <option key={y.value} value={y.value}>{y.label}</option>)}
                            </select>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );

    return (
        <div className="filter-menu-overlay" onClick={onClose} ref={overlayRef}>
            <div className="filter-menu-container" onClick={e => e.stopPropagation()}>
                <div className="filter-menu-header">
                    <h2>Map Filters</h2>
                    <button className="close-btn" onClick={onClose}>&times;</button>
                </div>

                <FilterSection type="pins" title="Pins" />
                <FilterSection type="areas" title="Areas" />

                <div className="filter-actions">
                    <button className="reset-btn" onClick={handleReset}>Clear All</button>
                    <button className="apply-btn" onClick={handleApply}>Apply Filters</button>
                </div>
            </div>
        </div>
    );
};

export default FilterMenu;
