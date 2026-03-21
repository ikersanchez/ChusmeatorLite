import React, { useState, useEffect, useRef } from 'react';
import { Marker, Popup, Tooltip, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import { api } from '../../../api/apiService';

// Category definitions with labels and SVG paths for pin icons
const CATEGORIES = {
    crime: { label: 'Crime / Delinquency', icon: '🔫', svgPath: 'M17 2h-2V0h-2v2H9V0H7v2H5a2 2 0 00-2 2v2h18V4a2 2 0 00-2-2zM3 8v10a2 2 0 002 2h14a2 2 0 002-2V8H3zm4 8H5v-2h2v2zm0-4H5v-2h2v2zm4 4H9v-2h2v2zm0-4H9v-2h2v2zm4 4h-2v-2h2v2zm4-4h-2v-2h2v2z' },
    alcohol: { label: 'Alcohol / Partying', icon: '🍺', svgPath: 'M8 2L6 14h12l-2-12H8zM6 16v2h12v-2H6zM11 6v6m-2-4h4' },
    screaming: { label: 'Screaming / Disturbances', icon: '😱', svgPath: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-2-10c0-.55-.45-1-1-1s-1 .45-1 1 .45 1 1 1 1-.45 1-1zm6 0c0-.55-.45-1-1-1s-1 .45-1 1 .45 1 1 1 1-.45 1-1zm-3 5.5c-1.66 0-3-1.12-3-2.5h6c0 1.38-1.34 2.5-3 2.5z' },
    loud_music: { label: 'Loud Music', icon: '🎵', svgPath: 'M12 3v10.55A4 4 0 1014 17V7h4V3h-6zM10 19a2 2 0 110-4 2 2 0 010 4z' },
    traffic: { label: 'Traffic / Noise', icon: '🚗', svgPath: 'M18.92 6.01C18.72 5.42 18.16 5 17.5 5h-11c-.66 0-1.21.42-1.42 1.01L3 12v8c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-1h12v1c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-8l-2.08-5.99zM6.5 16c-.83 0-1.5-.67-1.5-1.5S5.67 13 6.5 13s1.5.67 1.5 1.5S7.33 16 6.5 16zm11 0c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zM5 11l1.5-4.5h11L19 11H5z' },
    poor_lighting: { label: 'Poor Lighting', icon: '💡', svgPath: 'M9 21c0 .55.45 1 1 1h4c.55 0 1-.45 1-1v-1H9v1zm3-19C8.14 2 5 5.14 5 9c0 2.38 1.19 4.47 3 5.74V17c0 .55.45 1 1 1h6c.55 0 1-.45 1-1v-2.26c1.81-1.27 3-3.36 3-5.74 0-3.86-3.14-7-7-7z' },
    dirty: { label: 'Dirty / Trash', icon: '🗑️', svgPath: 'M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z' },
    construction: { label: 'Construction / Roadworks', icon: '🚧', svgPath: 'M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z' },
    dangerous_animals: { label: 'Dangerous Animals', icon: '🐕', svgPath: 'M4.5 11.5c0 2 1.5 3.5 3.5 3.5h1v4h2v-4h2v4h2v-4h1c2 0 3.5-1.5 3.5-3.5V10H4.5v1.5zM12 3C9.5 3 7.5 4 6.5 5.5L5 7h14l-1.5-1.5C16.5 4 14.5 3 12 3zm-2 4c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1zm4 0c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1z' },
    general_warning: { label: 'General Warning', icon: '⚠️', svgPath: 'M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z' },
};

// Create a custom SVG icon for pins with category-specific shapes
const createCategoryIcon = (category, color) => {
    const colorMap = {
        blue: '#3b82f6',
        green: '#22c55e',
        red: '#ef4444'
    };
    const fill = colorMap[color] || colorMap.blue;
    const cat = CATEGORIES[category] || CATEGORIES.general_warning;

    const svg = `
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 52" width="36" height="47">
            <defs>
                <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
                    <feDropShadow dx="0" dy="1" stdDeviation="1.5" flood-opacity="0.3"/>
                </filter>
            </defs>
            <path fill="${fill}" filter="url(#shadow)" d="M20 0C9 0 0 9 0 20c0 11 20 32 20 32s20-21 20-32C40 9 31 0 20 0z"/>
            <circle cx="20" cy="18" r="13" fill="white" opacity="0.9"/>
            <text x="20" y="24" text-anchor="middle" font-size="16" dominant-baseline="middle">${cat.icon}</text>
        </svg>
    `;

    return L.divIcon({
        className: 'custom-pin-icon',
        html: svg,
        iconSize: [36, 47],
        iconAnchor: [18, 47],
        popupAnchor: [0, -47],
        tooltipAnchor: [18, -34]
    });
};

const VOTE_THRESHOLD_PERMANENT_LABEL = 5;

const PinInteraction = ({ mode, filters, pins, setPins }) => {
    const [newPin, setNewPin] = useState(null);
    const [editingPin, setEditingPin] = useState(null);
    const [selectedCategory, setSelectedCategory] = useState('');
    const [selectedColor, setSelectedColor] = useState('blue');
    const [currentUserId, setCurrentUserId] = useState('');
    const [error, setError] = useState(null);

    // Ref for stopping leaflet propagation
    const modalRef = useRef(null);

    // Memoized filtered pins for performance
    const filteredPins = React.useMemo(() => {
        return pins.filter(pin => {
            // Color filter
            if (filters.color === 'none') {
                return false;
            }
            if (filters.color !== 'all' && pin.color !== filters.color) {
                return false;
            }

            // Category filter
            if (filters.category && filters.category !== 'all' && pin.category !== filters.category) {
                return false;
            }

            // Date range filter
            if (filters.startMonth || filters.startYear || filters.endMonth || filters.endYear) {
                const pinDate = new Date(pin.createdAt);
                const pinYearMonth = pinDate.getFullYear() * 100 + (pinDate.getMonth() + 1);

                if (filters.startMonth && filters.startYear) {
                    const startVal = parseInt(filters.startYear) * 100 + parseInt(filters.startMonth);
                    if (pinYearMonth < startVal) return false;
                }
                if (filters.endMonth && filters.endYear) {
                    const endVal = parseInt(filters.endYear) * 100 + parseInt(filters.endMonth);
                    if (pinYearMonth > endVal) return false;
                }
            }

            return true;
        });
    }, [pins, filters]);

    // Stop propagation on Modal
    useEffect(() => {
        if (modalRef.current) {
            L.DomEvent.disableClickPropagation(modalRef.current);
            L.DomEvent.disableScrollPropagation(modalRef.current);
        }
    }, [newPin, editingPin]);

    // Load user ID on mount
    useEffect(() => {
        const loadUserId = async () => {
            const userId = await api.getUserId();
            setCurrentUserId(userId);
        };
        loadUserId();
    }, []);

    // Handle map clicks to drop a temporary pin (only in PIN mode)
    useMapEvents({
        click(e) {
            if (mode !== 'PIN' || newPin || editingPin) return;

            setNewPin({
                lat: e.latlng.lat,
                lng: e.latlng.lng,
            });
            setSelectedCategory('');
            setError(null);
        },
    });

    const handleSave = async (e) => {
        if (e) e.preventDefault();
        if (!newPin || !selectedCategory) return;

        try {
            const savedPin = await api.savePin({
                lat: newPin.lat,
                lng: newPin.lng,
                category: selectedCategory,
                color: selectedColor,
            });

            setPins([...pins, savedPin]);
            setNewPin(null);
            setError(null);
        } catch (err) {
            console.error('Save pin error:', err);
            setError(err.message || 'Failed to save pin.');
        }
    };

    const handleUpdate = async (e) => {
        if (e) e.preventDefault();
        if (!editingPin || !selectedCategory) return;

        try {
            const pinToUpdate = pins.find(p => p.id === editingPin);
            const updatedPin = await api.updatePin(editingPin, {
                lat: pinToUpdate.lat,
                lng: pinToUpdate.lng,
                category: selectedCategory,
                color: selectedColor,
            });

            setPins(pins.map(p => p.id === editingPin
                ? { ...updatedPin, voteColors: p.voteColors, userVoteColor: p.userVoteColor }
                : p
            ));
            setEditingPin(null);
            setError(null);
        } catch (err) {
            console.error('Update pin error:', err);
            setError(err.message || 'Failed to update pin.');
        }
    };

    const handleCancel = () => {
        setNewPin(null);
        setEditingPin(null);
        setError(null);
    };

    const handleDelete = async (pinId) => {
        try {
            await api.deletePin(pinId);
            setPins(pins.filter(p => p.id !== pinId));
        } catch (error) {
            alert(error.message);
        }
    };

    const handleColorVote = async (pin, voteColor) => {
        try {
            const currentVote = pin.userVoteColor;
            if (currentVote === voteColor) {
                // Same color — remove vote
                await api.unvote('pin', pin.id);
                const newVoteColors = { ...pin.voteColors };
                newVoteColors[voteColor] = Math.max(0, (newVoteColors[voteColor] || 0) - 1);
                setPins(pins.map(p =>
                    p.id === pin.id ? { ...p, voteColors: newVoteColors, userVoteColor: null } : p
                ));
            } else {
                // New vote or change
                try {
                    await api.vote('pin', pin.id, voteColor);
                } catch (e) {
                    // 200 means vote was toggled off (shouldn't happen here but handle it)
                    if (e.message && e.message.includes('Vote removed')) {
                        const newVoteColors = { ...pin.voteColors };
                        newVoteColors[voteColor] = Math.max(0, (newVoteColors[voteColor] || 0) - 1);
                        setPins(pins.map(p =>
                            p.id === pin.id ? { ...p, voteColors: newVoteColors, userVoteColor: null } : p
                        ));
                        return;
                    }
                    throw e;
                }
                const newVoteColors = { ...pin.voteColors };
                if (currentVote) {
                    newVoteColors[currentVote] = Math.max(0, (newVoteColors[currentVote] || 0) - 1);
                }
                newVoteColors[voteColor] = (newVoteColors[voteColor] || 0) + 1;
                setPins(pins.map(p =>
                    p.id === pin.id ? { ...p, voteColors: newVoteColors, userVoteColor: voteColor } : p
                ));
            }
        } catch (error) {
            console.error('Vote error:', error);
        }
    };

    const getVoteTotal = (pin) => {
        const vc = pin.voteColors || {};
        return (vc.red || 0) + (vc.blue || 0) + (vc.green || 0);
    };

    const getVotePercentage = (pin, color) => {
        const total = getVoteTotal(pin);
        if (total === 0) return 0;
        return Math.round(((pin.voteColors?.[color] || 0) / total) * 100);
    };

    const getCategoryLabel = (category) => {
        return CATEGORIES[category]?.label || category;
    };

    const getCategoryIcon = (category) => {
        return CATEGORIES[category]?.icon || '⚠️';
    };

    const VoteColorButton = ({ pin, color }) => {
        const colorMap = { blue: '#3b82f6', green: '#22c55e', red: '#ef4444' };
        const isActive = pin.userVoteColor === color;
        const pct = getVotePercentage(pin, color);
        const count = pin.voteColors?.[color] || 0;
        return (
            <div
                onClick={(e) => { e.stopPropagation(); handleColorVote(pin, color); }}
                style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    cursor: 'pointer',
                    gap: '2px',
                }}
            >
                <div style={{
                    width: '28px',
                    height: '28px',
                    borderRadius: '50%',
                    backgroundColor: colorMap[color],
                    border: isActive ? '3px solid var(--text)' : '2px solid rgba(0,0,0,0.15)',
                    transition: 'all 0.2s ease',
                    transform: isActive ? 'scale(1.15)' : 'scale(1)',
                    boxShadow: isActive ? `0 0 8px ${colorMap[color]}66` : 'none',
                }} />
                <span style={{
                    fontSize: '0.65rem',
                    fontWeight: 600,
                    color: colorMap[color],
                }}>{count} ({pct}%)</span>
            </div>
        );
    };

    const ColorButton = ({ c, label }) => (
        <div
            onClick={(e) => {
                e.stopPropagation();
                setSelectedColor(c);
            }}
            style={{
                width: '30px',
                height: '30px',
                borderRadius: '50%',
                backgroundColor: c === 'blue' ? '#3b82f6' : c === 'green' ? '#22c55e' : '#ef4444',
                border: selectedColor === c ? '3px solid var(--text)' : '2px solid transparent',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
            }}
            title={label}
        />
    );


    return (
        <>
            {/* Existing saved pins */}
            {filteredPins.map((pin) => {
                const isOwner = pin.userId === currentUserId;
                const totalVotes = getVoteTotal(pin);
                const showPermanentLabel = totalVotes >= VOTE_THRESHOLD_PERMANENT_LABEL;

                return (
                    <Marker
                        key={pin.id}
                        position={[pin.lat, pin.lng]}
                        icon={createCategoryIcon(
                            pin.category,
                            pin.id === editingPin ? selectedColor : pin.color
                        )}
                    >
                        {/* Show permanent tooltip for highly-voted pins */}
                        {showPermanentLabel && (
                            <Tooltip
                                permanent
                                direction="top"
                                offset={[0, -46]}
                                className="modern-tooltip"
                            >
                                <div
                                    className="map-label-style"
                                    style={{ fontSize: '12px' }}
                                >
                                    {getCategoryIcon(pin.category)} {getCategoryLabel(pin.category)}
                                </div>
                            </Tooltip>
                        )}

                        <Popup className="premium-popup">
                            <div className="popup-content">
                                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                                    <span style={{ fontSize: '1.3rem' }}>{getCategoryIcon(pin.category)}</span>
                                    <strong>{getCategoryLabel(pin.category)}</strong>
                                </div>
                                <small style={{ color: '#666' }}>
                                    {new Date(pin.createdAt).toLocaleDateString()}
                                </small>

                                {/* Color vote buttons */}
                                <div style={{ marginTop: '10px' }}>
                                    <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                                        Vote Color
                                    </div>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '14px', justifyContent: 'center' }}>
                                        <VoteColorButton pin={pin} color="red" />
                                        <VoteColorButton pin={pin} color="blue" />
                                        <VoteColorButton pin={pin} color="green" />
                                    </div>
                                    {totalVotes > 0 && (
                                        <div style={{ fontSize: '0.7rem', color: '#9ca3af', textAlign: 'center', marginTop: '4px' }}>
                                            {totalVotes} total vote{totalVotes !== 1 ? 's' : ''}
                                        </div>
                                    )}
                                </div>

                                {isOwner && (
                                    <div style={{ marginTop: '8px' }}>
                                        <button
                                            onClick={() => handleDelete(pin.id)}
                                            style={{
                                                padding: '4px 8px',
                                                background: '#ef4444',
                                                color: 'white',
                                                border: 'none',
                                                borderRadius: '4px',
                                                cursor: 'pointer',
                                                fontSize: '0.85rem'
                                            }}
                                        >
                                            🗑️ Delete
                                        </button>
                                        <button
                                            onClick={() => {
                                                setEditingPin(pin.id);
                                                setSelectedCategory(pin.category);
                                                setSelectedColor(pin.color);
                                            }}
                                            style={{
                                                padding: '4px 8px',
                                                background: '#3b82f6',
                                                color: 'white',
                                                border: 'none',
                                                borderRadius: '4px',
                                                cursor: 'pointer',
                                                fontSize: '0.85rem',
                                                marginLeft: '8px'
                                            }}
                                        >
                                            ✏️ Edit
                                        </button>
                                    </div>
                                )}
                            </div>
                        </Popup>
                    </Marker>
                );
            })}

            {/* Temporary pin being created or Pin being edited — use bottom sheet style */}
            {(newPin || editingPin) && (
                <>
                    {newPin && <Marker position={[newPin.lat, newPin.lng]} icon={createCategoryIcon(selectedCategory || 'general_warning', selectedColor)} />}

                    <div
                        ref={modalRef}
                        style={{
                            position: 'fixed',
                            bottom: 0,
                            left: 0,
                            right: 0,
                            zIndex: 9999,
                            background: 'rgba(255,255,255,0.96)',
                            backdropFilter: 'blur(20px)',
                            WebkitBackdropFilter: 'blur(20px)',
                            padding: '12px 20px',
                            paddingBottom: 'max(12px, env(safe-area-inset-bottom))',
                            borderRadius: '20px 20px 0 0',
                            boxShadow: '0 -8px 40px rgba(0,0,0,0.12)',
                            maxWidth: '480px',
                            margin: '0 auto',
                        }}
                    >
                        <div style={{
                            width: '36px',
                            height: '4px',
                            background: '#d1d5db',
                            borderRadius: '2px',
                            margin: '0 auto 12px',
                        }} />
                        <h3 style={{ margin: '0 0 10px 0', fontSize: '1rem', fontWeight: 700 }}>
                            {editingPin ? 'Edit Pin' : 'Add Pin'}
                        </h3>

                        {error && (
                            <div style={{
                                padding: '8px 10px',
                                marginBottom: '10px',
                                background: '#fef2f2',
                                color: '#b91c1c',
                                border: '1px solid #fecaca',
                                borderRadius: '8px',
                                fontSize: '0.8rem'
                            }}>
                                {error}
                            </div>
                        )}

                        <form onSubmit={editingPin ? handleUpdate : handleSave}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                                <label style={{ fontSize: '0.8rem', fontWeight: '600', color: 'var(--text-secondary)' }}>
                                    Color
                                </label>
                                <div style={{ display: 'flex', gap: '12px' }}>
                                    <ColorButton c="blue" label="Blue" />
                                    <ColorButton c="green" label="Green" />
                                    <ColorButton c="red" label="Red" />
                                </div>
                            </div>

                            <div style={{ marginBottom: '10px' }}>
                                <label style={{ fontSize: '0.8rem', fontWeight: '600', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                                    Category
                                </label>
                                <select
                                    value={selectedCategory}
                                    onChange={(e) => setSelectedCategory(e.target.value)}
                                    style={{
                                        width: '100%',
                                        padding: '10px 12px',
                                        borderRadius: '10px',
                                        border: '1px solid rgba(0,0,0,0.1)',
                                        fontSize: '16px',
                                        background: 'rgba(0,0,0,0.02)',
                                        boxSizing: 'border-box',
                                        outline: 'none',
                                        appearance: 'none',
                                        WebkitAppearance: 'none',
                                        backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23666' d='M6 8L1 3h10z'/%3E%3C/svg%3E")`,
                                        backgroundRepeat: 'no-repeat',
                                        backgroundPosition: 'right 12px center',
                                        paddingRight: '32px',
                                        cursor: 'pointer',
                                    }}
                                >
                                    <option value="" disabled>Select a category...</option>
                                    {Object.entries(CATEGORIES).map(([key, cat]) => (
                                        <option key={key} value={key}>
                                            {cat.icon} {cat.label}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginBottom: '12px', textAlign: 'right' }}>
                                Get <strong>5 votes</strong> to make it permanent!
                            </div>

                            <div style={{ display: 'flex', gap: '8px' }}>
                                <button
                                    type="button"
                                    onClick={handleCancel}
                                    style={{
                                        flex: 1,
                                        padding: '10px',
                                        background: '#f1f5f9',
                                        border: 'none',
                                        borderRadius: '10px',
                                        cursor: 'pointer',
                                        fontWeight: '600',
                                        fontSize: '14px',
                                        color: 'var(--text)',
                                    }}
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    disabled={!selectedCategory}
                                    style={{
                                        flex: 2,
                                        padding: '10px',
                                        background: !selectedCategory ? '#ccc' : 'var(--accent)',
                                        color: 'white',
                                        border: 'none',
                                        borderRadius: '10px',
                                        cursor: !selectedCategory ? 'not-allowed' : 'pointer',
                                        fontWeight: 'bold',
                                        fontSize: '14px',
                                        boxShadow: !selectedCategory ? 'none' : '0 2px 10px rgba(59,130,246,0.3)',
                                    }}
                                >
                                    {editingPin ? 'Save Changes' : 'Save Pin'}
                                </button>
                            </div>
                        </form>
                    </div>
                </>
            )}
        </>
    );
};

export default PinInteraction;
