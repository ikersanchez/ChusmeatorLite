import React, { useState, useEffect, useCallback, useRef } from 'react';
import { FeatureGroup, Polygon, Polyline, CircleMarker, Tooltip, Popup, useMap, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import { api } from '../../../api/apiService';
import * as turf from '@turf/turf';

// Category definitions (same as PinInteraction)
const CATEGORIES = {
    crime: { label: 'Crime / Delinquency', icon: '🔫' },
    alcohol: { label: 'Alcohol / Partying', icon: '🍺' },
    screaming: { label: 'Screaming / Disturbances', icon: '😱' },
    loud_music: { label: 'Loud Music', icon: '🎵' },
    traffic: { label: 'Traffic / Noise', icon: '🚗' },
    poor_lighting: { label: 'Poor Lighting', icon: '💡' },
    dirty: { label: 'Dirty / Trash', icon: '🗑️' },
    construction: { label: 'Construction / Roadworks', icon: '🚧' },
    dangerous_animals: { label: 'Dangerous Animals', icon: '🐕' },
    general_warning: { label: 'General Warning', icon: '⚠️' },
};

const AreaInteraction = ({ mode, filters, areas, setAreas }) => {
    const [currentLayer, setCurrentLayer] = useState(null);
    const [editingArea, setEditingArea] = useState(null);
    const [color, setColor] = useState('blue');
    const [selectedCategory, setSelectedCategory] = useState('');
    const [isDrawing, setIsDrawing] = useState(false);
    const [error, setError] = useState(null);
    const MAX_AREA_SIZE_DEG = 0.02;

    // Manual drawing state
    const [drawPoints, setDrawPoints] = useState([]);
    const [isManualDrawing, setIsManualDrawing] = useState(false);

    const [currentUserId, setCurrentUserId] = useState('');

    const map = useMap();
    
    // Refs for stopping leaflet propagation
    const hudRef = useRef(null);
    const modalRef = useRef(null);

    // Memoized filtered areas for performance
    const filteredAreas = React.useMemo(() => {
        return areas.filter(area => {
            // Color filter
            if (filters.color === 'none') {
                return false;
            }
            if (filters.color !== 'all' && area.color !== filters.color) {
                return false;
            }

            // Category filter
            if (filters.category && filters.category !== 'all' && area.category !== filters.category) {
                return false;
            }

            // Date range filter
            if (filters.startMonth || filters.startYear || filters.endMonth || filters.endYear) {
                const areaDate = new Date(area.createdAt);
                const areaYearMonth = areaDate.getFullYear() * 100 + (areaDate.getMonth() + 1);

                if (filters.startMonth && filters.startYear) {
                    const startVal = parseInt(filters.startYear) * 100 + parseInt(filters.startMonth);
                    if (areaYearMonth < startVal) return false;
                }
                if (filters.endMonth && filters.endYear) {
                    const endVal = parseInt(filters.endYear) * 100 + parseInt(filters.endMonth);
                    if (areaYearMonth > endVal) return false;
                }
            }

            return true;
        });
    }, [areas, filters]);

    // Stop propagation on HUD and Modal
    useEffect(() => {
        if (hudRef.current) {
            L.DomEvent.disableClickPropagation(hudRef.current);
            L.DomEvent.disableScrollPropagation(hudRef.current);
        }
        if (modalRef.current) {
            L.DomEvent.disableClickPropagation(modalRef.current);
            L.DomEvent.disableScrollPropagation(modalRef.current);
        }
    }, [isManualDrawing, isDrawing, currentLayer, editingArea]);

    // Load user ID on mount
    useEffect(() => {
        const loadUserId = async () => {
            const userId = await api.getUserId();
            setCurrentUserId(userId);
        };
        loadUserId();
    }, []);

    // Auto-start manual drawing when switching to AREA mode
    useEffect(() => {
        if (mode === 'AREA' && !isDrawing && !isManualDrawing) {
            setIsManualDrawing(true);
            setDrawPoints([]);
        }
        if (mode !== 'AREA') {
            // If user switches away, cancel drawing
            setIsManualDrawing(false);
            setDrawPoints([]);
        }
    }, [mode, isDrawing, isManualDrawing]);

    const handleFinishDraw = useCallback((points = drawPoints) => {
        if (points.length < 3) return;

        // Validate size
        const lats = points.map(p => p[0]);
        const lngs = points.map(p => p[1]);
        const latDelta = Math.max(...lats) - Math.min(...lats);
        const lngDelta = Math.max(...lngs) - Math.min(...lngs);

        if (Math.max(latDelta, lngDelta) > MAX_AREA_SIZE_DEG) {
            setError("This area is a bit big! We try to keep things neighborhood-sized for a better experience.");
        } else {
            // Overlap check
            const isOverlapping = checkOverlapFromPoints(points);
            if (isOverlapping) {
                setError("Whoops! This area overlaps with an existing one. Try drawing in a clear spot!");
            } else {
                setError(null);
            }
        }

        // Store the polygon points and show form
        setCurrentLayer(points);
        setIsDrawing(true);
        setIsManualDrawing(false);
    }, [drawPoints, areas]);

    // Handle map clicks for manual drawing
    useMapEvents({
        click(e) {
            if (mode !== 'AREA' || !isManualDrawing || isDrawing || editingArea) return;

            // Check proximity to start point if we have at least 3 points
            if (drawPoints.length >= 3) {
                const startPoint = drawPoints[0];
                const startPx = map.latLngToLayerPoint([startPoint[0], startPoint[1]]);
                const currentPx = map.latLngToLayerPoint(e.latlng);
                const distance = startPx.distanceTo(currentPx);

                // If clicked within 25 pixels of the start point, close the area
                if (distance < 25) {
                    handleFinishDraw(drawPoints);
                    return;
                }
            }

            setDrawPoints(prev => [...prev, [e.latlng.lat, e.latlng.lng]]);
        }
    });

    const handleUndoPoint = useCallback(() => {
        setDrawPoints(prev => prev.slice(0, -1));
    }, []);

    const handleCancelDraw = useCallback(() => {
        setDrawPoints([]);
        setIsManualDrawing(false);
    }, []);

    const handleSave = async (e) => {
        e.preventDefault();
        setError(null);
        if (!currentLayer || !selectedCategory) return;

        let latlngs;
        let latDiff, lngDiff;

        if (Array.isArray(currentLayer)) {
            // Manual drawing — currentLayer is array of [lat, lng]
            latlngs = [currentLayer.map(p => ({ lat: p[0], lng: p[1] }))];
            const lats = currentLayer.map(p => p[0]);
            const lngs = currentLayer.map(p => p[1]);
            latDiff = Math.max(...lats) - Math.min(...lats);
            lngDiff = Math.max(...lngs) - Math.min(...lngs);
        } else {
            // Legacy leaflet-draw layer
            const bounds = currentLayer.getBounds();
            const northEast = bounds.getNorthEast();
            const southWest = bounds.getSouthWest();
            latDiff = Math.abs(northEast.lat - southWest.lat);
            lngDiff = Math.abs(northEast.lng - southWest.lng);
            latlngs = currentLayer.getLatLngs();
        }

        // Client-side size validation
        if (Math.max(latDiff, lngDiff) > MAX_AREA_SIZE_DEG) {
            setError("Whoops, that's a huge area! Let's keep it local—try drawing a smaller neighborhood instead.");
            return;
        }

        // Rough heuristic for font size based on lat diff
        const fontSize = Math.round(Math.max(14, Math.min(48, latDiff * 2000))) + 'px';

        const newArea = {
            latlngs,
            color,
            category: selectedCategory,
            fontSize,
        };

        try {
            const savedArea = await api.saveArea(newArea);
            setAreas([...areas, savedArea]);

            // Cleanup
            if (!Array.isArray(currentLayer) && currentLayer.remove) {
                currentLayer.remove();
            }
            setCurrentLayer(null);
            setIsDrawing(false);
            setDrawPoints([]);
            setSelectedCategory('');
            setError(null);
        } catch (err) {
            console.error('Save area error:', err);
            setError(err.message || 'Failed to save area. It might be too large or you reached your daily limit.');
        }
    };

    const handleUpdate = async (e) => {
        e.preventDefault();
        setError(null);
        if (!editingArea || !selectedCategory) return;

        const updatedAreaPayload = {
            color,
            category: selectedCategory,
        };

        try {
            const updatedArea = await api.updateArea(editingArea, updatedAreaPayload);
            setAreas(areas.map(a => a.id === editingArea
                ? { ...updatedArea, voteColors: a.voteColors, userVoteColor: a.userVoteColor }
                : a
            ));

            // Cleanup
            setCurrentLayer(null);
            setIsDrawing(false);
            setEditingArea(null);
            setDrawPoints([]);
            setSelectedCategory('');
            setError(null);
        } catch (err) {
            console.error('Update area error:', err);
            setError(err.message || 'Failed to update area.');
        }
    };

    const handleCancel = () => {
        if (currentLayer && !Array.isArray(currentLayer) && currentLayer.remove) {
            currentLayer.remove();
        }
        setCurrentLayer(null);
        setIsDrawing(false);
        setDrawPoints([]);
        setSelectedCategory('');
        setEditingArea(null);
        setError(null);
        // Re-enter drawing mode
        if (mode === 'AREA') {
            setIsManualDrawing(true);
        }
    };

    const handleDelete = async (areaId) => {
        try {
            await api.deleteArea(areaId);
            setAreas(areas.filter(a => a.id !== areaId));
        } catch (error) {
            alert(error.message);
        }
    };

    const handleColorVote = async (area, voteColor) => {
        try {
            const currentVote = area.userVoteColor;
            if (currentVote === voteColor) {
                // Same color — remove vote
                await api.unvote('area', area.id);
                const newVoteColors = { ...area.voteColors };
                newVoteColors[voteColor] = Math.max(0, (newVoteColors[voteColor] || 0) - 1);
                setAreas(areas.map(a =>
                    a.id === area.id ? { ...a, voteColors: newVoteColors, userVoteColor: null } : a
                ));
            } else {
                try {
                    await api.vote('area', area.id, voteColor);
                } catch (e) {
                    if (e.message && e.message.includes('Vote removed')) {
                        const newVoteColors = { ...area.voteColors };
                        newVoteColors[voteColor] = Math.max(0, (newVoteColors[voteColor] || 0) - 1);
                        setAreas(areas.map(a =>
                            a.id === area.id ? { ...a, voteColors: newVoteColors, userVoteColor: null } : a
                        ));
                        return;
                    }
                    throw e;
                }
                const newVoteColors = { ...area.voteColors };
                if (currentVote) {
                    newVoteColors[currentVote] = Math.max(0, (newVoteColors[currentVote] || 0) - 1);
                }
                newVoteColors[voteColor] = (newVoteColors[voteColor] || 0) + 1;
                setAreas(areas.map(a =>
                    a.id === area.id ? { ...a, voteColors: newVoteColors, userVoteColor: voteColor } : a
                ));
            }
        } catch (error) {
            console.error('Vote error:', error);
        }
    };

    const getVoteTotal = (area) => {
        const vc = area.voteColors || {};
        return (vc.red || 0) + (vc.blue || 0) + (vc.green || 0);
    };

    const getVotePercentage = (area, color) => {
        const total = getVoteTotal(area);
        if (total === 0) return 0;
        return Math.round(((area.voteColors?.[color] || 0) / total) * 100);
    };

    const checkOverlapFromPoints = (points) => {
        try {
            const coords = points.map(p => [p[1], p[0]]); // [lng, lat]
            coords.push(coords[0]); // close polygon
            const newPoly = turf.polygon([coords]);

            return areas.some(area => {
                try {
                    let areaCoords;
                    if (Array.isArray(area.latlngs[0])) {
                        areaCoords = area.latlngs[0].map(ll => [ll.lng, ll.lat]);
                    } else {
                        areaCoords = area.latlngs.map(ll => [ll.lng, ll.lat]);
                    }
                    if (areaCoords.length < 3) return false;
                    areaCoords.push(areaCoords[0]);
                    const existingPoly = turf.polygon([areaCoords]);
                    const intersection = turf.intersect(turf.featureCollection([newPoly, existingPoly]));
                    return intersection !== null;
                } catch (e) {
                    console.error("Error checking overlap with area", area.id, e);
                    return false;
                }
            });
        } catch (e) {
            console.error("Error in checkOverlapFromPoints", e);
            return false;
        }
    };

    const getVoteFontSize = (area) => {
        const basePx = parseFloat(area.fontSize) || 14;
        const totalVotes = getVoteTotal(area);
        const boost = 1 + Math.min(totalVotes, 50) * 0.02;
        return basePx * boost + 'px';
    };

    const getCategoryLabel = (category) => {
        return CATEGORIES[category]?.label || category;
    };

    const getCategoryIcon = (category) => {
        return CATEGORIES[category]?.icon || '⚠️';
    };

    const VoteColorButton = ({ area, voteColor }) => {
        const colorMap = { blue: '#3b82f6', green: '#22c55e', red: '#ef4444' };
        const isActive = area.userVoteColor === voteColor;
        const pct = getVotePercentage(area, voteColor);
        const count = area.voteColors?.[voteColor] || 0;
        return (
            <div
                onClick={(e) => { e.stopPropagation(); handleColorVote(area, voteColor); }}
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
                    backgroundColor: colorMap[voteColor],
                    border: isActive ? '3px solid var(--text)' : '2px solid rgba(0,0,0,0.15)',
                    transition: 'all 0.2s ease',
                    transform: isActive ? 'scale(1.15)' : 'scale(1)',
                    boxShadow: isActive ? `0 0 8px ${colorMap[voteColor]}66` : 'none',
                }} />
                <span style={{
                    fontSize: '0.65rem',
                    fontWeight: 600,
                    color: colorMap[voteColor],
                }}>{count} ({pct}%)</span>
            </div>
        );
    };

    const ColorButton = ({ c, label }) => (
        <button
            type="button"
            onClick={(e) => {
                e.stopPropagation();
                setColor(c);
            }}
            style={{
                backgroundColor: c === 'blue' ? 'rgba(59, 130, 246, 0.6)' : c === 'green' ? 'rgba(34, 197, 94, 0.6)' : 'rgba(239, 68, 68, 0.6)',
                border: color === c ? '3px solid var(--text)' : '2px solid transparent',
                width: '32px',
                height: '32px',
                borderRadius: '50%',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                flexShrink: 0,
            }}
            title={label}
        />
    );

    return (
        <FeatureGroup>
            {/* Render saved areas */}
            {filteredAreas.map((area) => {
                const isOwner = area.userId === currentUserId;
                const colorHex = area.color === 'blue' ? '#3b82f6' : area.color === 'green' ? '#22c55e' : '#ef4444';
                const totalVotes = getVoteTotal(area);

                return (
                    <Polygon
                        key={area.id}
                        positions={area.latlngs}
                        pathOptions={{
                            color: colorHex,
                            fillOpacity: 0.4,
                            interactive: mode !== 'PIN'
                        }}
                    >
                        <Tooltip
                            permanent
                            direction="center"
                            className="modern-tooltip"
                            offset={[0, 0]}
                            interactive={mode !== 'PIN'}
                        >
                            <div
                                className="map-label-style"
                                style={{
                                    fontSize: getVoteFontSize(area),
                                    opacity: editingArea === area.id ? 0.3 : 1
                                }}
                            >
                                {getCategoryIcon(area.category)} {getCategoryLabel(area.category)}
                            </div>
                        </Tooltip>

                        {mode !== 'PIN' && editingArea !== area.id && (
                            <Popup>
                                <div>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                                        <span style={{ fontSize: '1.3rem' }}>{getCategoryIcon(area.category)}</span>
                                        <strong>{getCategoryLabel(area.category)}</strong>
                                    </div>
                                    <small>{new Date(area.createdAt).toLocaleDateString()}</small>

                                    {/* Color vote buttons */}
                                    <div style={{ marginTop: '10px' }}>
                                        <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                                            Vote Color
                                        </div>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '14px', justifyContent: 'center' }}>
                                            <VoteColorButton area={area} voteColor="red" />
                                            <VoteColorButton area={area} voteColor="blue" />
                                            <VoteColorButton area={area} voteColor="green" />
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
                                                onClick={() => handleDelete(area.id)}
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
                                                    setEditingArea(area.id);
                                                    setSelectedCategory(area.category);
                                                    setColor(area.color);
                                                    setCurrentLayer(area.latlngs);
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
                        )}
                    </Polygon>
                );
            })}

            {/* Visual feedback while manually drawing */}
            {isManualDrawing && drawPoints.length >= 2 && (
                <Polyline
                    positions={drawPoints}
                    pathOptions={{ color: '#3b82f6', weight: 3, dashArray: '8, 8' }}
                />
            )}
            {isManualDrawing && drawPoints.length >= 3 && (
                <Polygon
                    positions={drawPoints}
                    pathOptions={{ color: '#3b82f6', fillOpacity: 0.15, weight: 1, dashArray: '4, 4' }}
                />
            )}
            {isManualDrawing && drawPoints.map((pt, i) => (
                <CircleMarker
                    key={i}
                    center={pt}
                    radius={i === 0 ? 10 : 6}
                    pathOptions={{
                        color: i === 0 ? '#3b82f6' : '#fff',
                        weight: 2,
                        fillColor: i === 0 ? '#fff' : '#3b82f6',
                        fillOpacity: 1
                    }}
                >
                    {i === 0 && drawPoints.length >= 3 && (
                        <Tooltip permanent direction="top" className="start-point-tooltip">
                            Tap here to finish
                        </Tooltip>
                    )}
                </CircleMarker>
            ))}

            {/* In-progress drawing preview for finalized polygon OR editing area polygon */}
            {(isDrawing && Array.isArray(currentLayer) || editingArea && currentLayer) && (
                <Polygon
                    positions={currentLayer}
                    pathOptions={{ color: '#3b82f6', fillOpacity: 0.3 }}
                />
            )}

            {/* ─── Drawing HUD (bottom bar while tapping points) ─── */}
            {isManualDrawing && (
                <div
                    ref={hudRef}
                    style={{
                        position: 'fixed',
                        bottom: '80px',
                        left: '50%',
                        transform: 'translateX(-50%)',
                        zIndex: 1100,
                        display: 'flex',
                        alignItems: 'center',
                        gap: '12px',
                        background: 'rgba(255,255,255,0.9)',
                        backdropFilter: 'blur(12px)',
                        WebkitBackdropFilter: 'blur(12px)',
                        padding: '10px 16px',
                        borderRadius: '16px',
                        boxShadow: '0 4px 24px rgba(0,0,0,0.12)',
                        border: '1px solid rgba(0,0,0,0.06)',
                    }}
                >
                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                        <span style={{
                            fontSize: '13px',
                            color: 'var(--text)',
                            fontWeight: 600,
                            whiteSpace: 'nowrap',
                        }}>
                            {drawPoints.length === 0 ? 'Start drawing' : `${drawPoints.length} Points`}
                        </span>
                        <span style={{ fontSize: '10px', color: 'var(--text-secondary)' }}>
                            {drawPoints.length < 3 ? 'Add 3+ points' : 'Tap start to finish'}
                        </span>
                    </div>

                    <div style={{ width: '1px', height: '24px', background: 'rgba(0,0,0,0.1)', margin: '0 4px' }} />

                    <button
                        onClick={(e) => { e.stopPropagation(); handleUndoPoint(); }}
                        disabled={drawPoints.length === 0}
                        style={{
                            padding: '8px 12px',
                            background: 'transparent',
                            color: drawPoints.length === 0 ? '#9ca3af' : 'var(--text)',
                            border: 'none',
                            borderRadius: '10px',
                            cursor: drawPoints.length === 0 ? 'default' : 'pointer',
                            fontWeight: 600,
                            fontSize: '13px',
                        }}
                    >
                        Undo
                    </button>
                    <button
                        onClick={(e) => { e.stopPropagation(); handleCancelDraw(); }}
                        style={{
                            padding: '8px 12px',
                            background: 'transparent',
                            color: '#ef4444',
                            border: 'none',
                            borderRadius: '10px',
                            cursor: 'pointer',
                            fontWeight: 600,
                            fontSize: '13px',
                        }}
                    >
                        Cancel
                    </button>
                </div>
            )}

            {/* ─── Configuration Modal for new area (modern bottom sheet style on mobile) ─── */}
            {((isDrawing && currentLayer) || editingArea) && (
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
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                        <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 700 }}>
                            {editingArea ? 'Edit Area' : 'Configure Area'}
                        </h3>
                    </div>

                    {error && (
                        <div style={{
                            padding: '8px 10px',
                            marginBottom: '10px',
                            background: error.includes('Warning') ? '#fff7ed' : '#fef2f2',
                            color: error.includes('Warning') ? '#c2410c' : '#b91c1c',
                            border: error.includes('Warning') ? '1px solid #fdba74' : '1px solid #fecaca',
                            borderRadius: '8px',
                            fontSize: '0.8rem'
                        }}>
                            {error.includes('Warning') ? '⚠️ ' : '🚫 '} {error}
                        </div>
                    )}

                    <form onSubmit={editingArea ? handleUpdate : handleSave}>
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
                                onChange={e => setSelectedCategory(e.target.value)}
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
                                autoFocus
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
                            More votes = <strong>BIGGER</strong> text!
                        </div>

                        <div style={{ display: 'flex', gap: '8px' }}>
                            <button
                                type="button"
                                onClick={(e) => { e.stopPropagation(); handleCancel(); }}
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
                                disabled={(!!error && !error.includes('Warning')) || !selectedCategory}
                                style={{
                                    flex: 2,
                                    padding: '10px',
                                    background: ((!!error && !error.includes('Warning')) || !selectedCategory) ? '#ccc' : 'var(--accent)',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '10px',
                                    cursor: ((!!error && !error.includes('Warning')) || !selectedCategory) ? 'not-allowed' : 'pointer',
                                    fontWeight: 'bold',
                                    fontSize: '14px',
                                    boxShadow: ((!!error && !error.includes('Warning')) || !selectedCategory) ? 'none' : '0 2px 10px rgba(59,130,246,0.3)',
                                }}
                            >
                                {editingArea ? 'Save Changes' : 'Save Area'}
                            </button>
                        </div>
                    </form>
                </div>
            )}
        </FeatureGroup>
    );
};

export default AreaInteraction;
