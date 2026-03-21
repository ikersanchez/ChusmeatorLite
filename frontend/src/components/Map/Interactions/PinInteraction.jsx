import React, { useState, useEffect, useRef } from 'react';
import { Marker, Popup, Tooltip, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import { api } from '../../../api/apiService';

// Create a custom SVG icon for pins with dynamic colors
const createColoredIcon = (color) => {
    // Map our semantic colors to hex values for the SVG
    const colorMap = {
        blue: '#3b82f6',
        green: '#22c55e',
        red: '#ef4444'
    };
    const fill = colorMap[color] || colorMap.blue;

    const svg = `
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 384 512" width="25" height="41">
            <path fill="${fill}" d="M172.268 501.67C26.97 291.031 0 269.413 0 192 0 85.961 85.961 0 192 0s192 85.961 192 192c0 77.413-26.97 99.031-172.268 309.67-9.535 13.774-29.93 13.773-39.464 0zM192 272c44.183 0 80-35.817 80-80s-35.817-80-80-80-80 35.817-80 80 35.817 80 80 80z"/>
        </svg>
    `;

    return L.divIcon({
        className: 'custom-pin-icon',
        html: svg,
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [0, -41],
        tooltipAnchor: [12, -28]
    });
};

const VOTE_THRESHOLD_PERMANENT_LABEL = 5;

const PinInteraction = ({ mode, filters, pins, setPins }) => {
    const [newPin, setNewPin] = useState(null);
    const [editingPin, setEditingPin] = useState(null); // ID of pin being edited
    const [formData, setFormData] = useState('');
    const [selectedColor, setSelectedColor] = useState('blue');
    const [currentUserId, setCurrentUserId] = useState('');
    const [error, setError] = useState(null);

    // Comments state
    const [commentsVisibleForPin, setCommentsVisibleForPin] = useState(null);
    const [pinComments, setPinComments] = useState({});
    const [newCommentText, setNewCommentText] = useState('');
    const [loadingComments, setLoadingComments] = useState(false);
    const [commentError, setCommentError] = useState(null);

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
            // FIX: If newPin already exists, don't drop a new one or reset form.
            // This prevented saving on mobile when clicks leaked through.
            if (mode !== 'PIN' || newPin || editingPin) return;

            setNewPin({
                lat: e.latlng.lat,
                lng: e.latlng.lng,
            });
            setFormData(''); // Reset form
            setError(null);
        },
    });

    const handleSave = async (e) => {
        if (e) e.preventDefault();
        if (!newPin || !formData.trim()) return;

        try {
            const savedPin = await api.savePin({
                lat: newPin.lat,
                lng: newPin.lng,
                text: formData,
                color: selectedColor,
            });

            setPins([...pins, savedPin]);
            setNewPin(null); // Clear temp pin
            setError(null);
        } catch (err) {
            console.error('Save pin error:', err);
            setError(err.message || 'Failed to save pin.');
        }
    };

    const handleUpdate = async (e) => {
        if (e) e.preventDefault();
        if (!editingPin || !formData.trim()) return;

        try {
            const pinToUpdate = pins.find(p => p.id === editingPin);
            const updatedPin = await api.updatePin(editingPin, {
                lat: pinToUpdate.lat,
                lng: pinToUpdate.lng,
                text: formData,
                color: selectedColor,
            });

            setPins(pins.map(p => p.id === editingPin
                ? { ...updatedPin, votes: p.votes, userVoteValue: p.userVoteValue, commentCount: p.commentCount }
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

    const handleVote = async (pin, value) => {
        try {
            const currentValue = pin.userVoteValue || 0;
            if (currentValue === value) {
                // Clicking the same button again removes the vote
                await api.unvote('pin', pin.id);
                setPins(pins.map(p =>
                    p.id === pin.id ? { ...p, votes: p.votes - value, userVoteValue: 0 } : p
                ));
            } else {
                // If switching from opposite vote, remove old vote first
                if (currentValue !== 0) {
                    await api.unvote('pin', pin.id);
                }
                await api.vote('pin', pin.id, value);
                setPins(pins.map(p =>
                    p.id === pin.id ? { ...p, votes: p.votes - currentValue + value, userVoteValue: value } : p
                ));
            }
        } catch (error) {
            console.error('Vote error:', error);
        }
    };

    const handleToggleComments = async (pinId) => {
        if (commentsVisibleForPin === pinId) {
            // Close comments
            setCommentsVisibleForPin(null);
            return;
        }

        // Open comments and fetch
        setCommentsVisibleForPin(pinId);
        setNewCommentText('');
        setCommentError(null);

        if (!pinComments[pinId]) {
            setLoadingComments(true);
            try {
                const comments = await api.getPinComments(pinId);
                setPinComments(prev => ({ ...prev, [pinId]: comments }));
            } catch (error) {
                console.error('Error fetching comments:', error);
            } finally {
                setLoadingComments(false);
            }
        }
    };

    const handleAddComment = async (e, pinId) => {
        e.preventDefault();
        if (!newCommentText.trim() || newCommentText.length > 100) return;

        try {
            const addedComment = await api.addPinComment(pinId, newCommentText);
            setPinComments(prev => ({
                ...prev,
                [pinId]: [addedComment, ...(prev[pinId] || [])]
            }));
            
            // Increment comment counter without refreshing
            setPins(prevPins => prevPins.map(p => 
                p.id === pinId 
                    ? { ...p, commentCount: (p.commentCount || 0) + 1 } 
                    : p
            ));
            
            setNewCommentText('');
            setCommentError(null);
        } catch (error) {
            console.error('Error adding comment:', error);
            setCommentError(error.message || 'Failed to post comment.');
        }
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
                const showPermanentLabel = pin.votes >= VOTE_THRESHOLD_PERMANENT_LABEL;

                return (
                    <Marker
                        key={pin.id}
                        position={[pin.lat, pin.lng]}
                        icon={createColoredIcon(pin.id === editingPin ? selectedColor : pin.color)}
                    >
                        {/* Show permanent tooltip for highly-voted pins */}
                        {showPermanentLabel && (
                            <Tooltip
                                permanent
                                direction="top"
                                offset={[0, -40]}
                                className="modern-tooltip"
                            >
                                <div
                                    className="map-label-style"
                                    style={{ fontSize: '12px' }}
                                >
                                    {pin.text}
                                </div>
                            </Tooltip>
                        )}

                        <Popup className="premium-popup">
                            <div className="popup-content">
                                <strong>Info:</strong> {pin.text} <br />
                                <small style={{ color: '#666' }}>
                                    {new Date(pin.createdAt).toLocaleDateString()}
                                </small>

                                {/* Vote buttons and Comments button */}
                                <div style={{ marginTop: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                                    <button
                                        onClick={() => handleVote(pin, 1)}
                                        className={`action-btn vote-btn ${pin.userVoteValue === 1 ? 'voted' : ''}`}
                                    >
                                        👍
                                    </button>
                                    <span style={{ fontWeight: 700, fontSize: '0.9rem', minWidth: '20px', textAlign: 'center', color: pin.votes > 0 ? '#22c55e' : pin.votes < 0 ? '#ef4444' : '#64748b' }}>
                                        {pin.votes}
                                    </span>
                                    <button
                                        onClick={() => handleVote(pin, -1)}
                                        className={`action-btn vote-btn dislike-btn ${pin.userVoteValue === -1 ? 'disliked' : ''}`}
                                    >
                                        👎
                                    </button>
                                    <button
                                        onClick={() => handleToggleComments(pin.id)}
                                        className="action-btn comment-btn"
                                    >
                                        💬 Comments {pin.commentCount > 0 && `(${pin.commentCount})`}
                                    </button>
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
                                                setFormData(pin.text);
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

                                {/* Comments Section */}
                                {commentsVisibleForPin === pin.id && (
                                    <div className="comments-section" style={{ marginTop: '12px', borderTop: '1px solid #eee', paddingTop: '8px' }}>
                                        <h4 style={{ margin: '0 0 8px 0', fontSize: '0.9rem' }}>Comments</h4>

                                        <div className="comments-list" style={{ maxHeight: '150px', overflowY: 'auto', marginBottom: '8px' }}>
                                            {loadingComments ? (
                                                <div style={{ fontSize: '0.8rem', color: '#666', textAlign: 'center' }}>Loading...</div>
                                            ) : pinComments[pin.id]?.length > 0 ? (
                                                pinComments[pin.id].map(comment => (
                                                    <div key={comment.id} style={{
                                                        background: '#f9fafb',
                                                        padding: '6px 8px',
                                                        borderRadius: '6px',
                                                        marginBottom: '6px',
                                                        fontSize: '0.85rem'
                                                    }}>
                                                        <div style={{ wordBreak: 'break-word' }}>{comment.text}</div>
                                                        <div style={{ fontSize: '0.7rem', color: '#9ca3af', marginTop: '2px', textAlign: 'right' }}>
                                                            {new Date(comment.createdAt).toLocaleDateString()} {new Date(comment.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                                        </div>
                                                    </div>
                                                ))
                                            ) : (
                                                <div style={{ fontSize: '0.8rem', color: '#666', textAlign: 'center', margin: '10px 0' }}>No comments yet.</div>
                                            )}
                                        </div>

                                        {commentError && (
                                            <div style={{
                                                padding: '6px 8px',
                                                marginBottom: '8px',
                                                background: '#fef2f2',
                                                color: '#b91c1c',
                                                border: '1px solid #fecaca',
                                                borderRadius: '6px',
                                                fontSize: '0.75rem'
                                            }}>
                                                {commentError}
                                            </div>
                                        )}

                                        <form onSubmit={(e) => handleAddComment(e, pin.id)} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                                            <input
                                                type="text"
                                                value={newCommentText}
                                                onChange={(e) => setNewCommentText(e.target.value)}
                                                placeholder="Write a comment..."
                                                maxLength={100}
                                                style={{
                                                    padding: '8px 12px',
                                                    borderRadius: '8px',
                                                    border: '1px solid #cbd5e1',
                                                    fontSize: '16px',
                                                    outline: 'none',
                                                }}
                                            />
                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                                <span style={{ fontSize: '0.7rem', color: newCommentText.length >= 100 ? '#ef4444' : '#9ca3af' }}>
                                                    {newCommentText.length}/100
                                                </span>
                                                <button
                                                    type="submit"
                                                    disabled={!newCommentText.trim() || newCommentText.length > 100}
                                                    style={{
                                                        padding: '4px 10px',
                                                        background: 'var(--accent)',
                                                        color: 'white',
                                                        border: 'none',
                                                        borderRadius: '6px',
                                                        cursor: !newCommentText.trim() || newCommentText.length > 100 ? 'not-allowed' : 'pointer',
                                                        fontSize: '0.85rem',
                                                        opacity: !newCommentText.trim() || newCommentText.length > 100 ? 0.5 : 1,
                                                        fontWeight: '600',
                                                    }}
                                                >
                                                    Post
                                                </button>
                                            </div>
                                        </form>
                                    </div>
                                )}
                            </div>
                        </Popup>
                    </Marker>
                );
            })}

            {/* Temporary pin being created or Pin being edited — use bottom sheet style — compact for mobile */}
            {(newPin || editingPin) && (
                <>
                    {newPin && <Marker position={[newPin.lat, newPin.lng]} icon={createColoredIcon(selectedColor)} />}

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

                            <textarea
                                value={formData}
                                onChange={(e) => setFormData(e.target.value)}
                                placeholder="e.g. 'Best Coffee'..."
                                maxLength={35}
                                style={{
                                    width: '100%',
                                    padding: '10px 12px',
                                    marginBottom: '6px',
                                    borderRadius: '10px',
                                    border: '1px solid rgba(0,0,0,0.1)',
                                    fontSize: '16px',
                                    background: 'rgba(0,0,0,0.02)',
                                    boxSizing: 'border-box',
                                    outline: 'none',
                                    minHeight: '64px',
                                    fontFamily: 'inherit',
                                    resize: 'none',
                                }}
                                autoFocus
                            />

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
                                    disabled={!formData.trim()}
                                    style={{
                                        flex: 2,
                                        padding: '10px',
                                        background: !formData.trim() ? '#ccc' : 'var(--accent)',
                                        color: 'white',
                                        border: 'none',
                                        borderRadius: '10px',
                                        cursor: !formData.trim() ? 'not-allowed' : 'pointer',
                                        fontWeight: 'bold',
                                        fontSize: '14px',
                                        boxShadow: !formData.trim() ? 'none' : '0 2px 10px rgba(59,130,246,0.3)',
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
