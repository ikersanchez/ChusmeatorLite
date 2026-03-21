import React, { useEffect, useRef } from 'react';
import L from 'leaflet';

const HelpModal = ({ onClose }) => {
    const overlayRef = useRef(null);

    useEffect(() => {
        if (overlayRef.current) {
            L.DomEvent.disableClickPropagation(overlayRef.current);
            L.DomEvent.disableScrollPropagation(overlayRef.current);
        }
    }, []);

    return (
        <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            width: '100vw',
            height: '100vh',
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            zIndex: 10000,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            backdropFilter: 'blur(5px)'
        }} onClick={onClose} ref={overlayRef}>
            <div style={{
                backgroundColor: 'white',
                padding: '30px',
                borderRadius: '16px',
                maxWidth: '500px',
                width: '90%',
                maxHeight: '90vh',
                overflowY: 'auto',
                boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
                position: 'relative'
            }} onClick={e => e.stopPropagation()}>

                <button
                    onClick={onClose}
                    style={{
                        position: 'absolute',
                        top: '15px',
                        right: '15px',
                        background: 'none',
                        border: 'none',
                        fontSize: '1.5rem',
                        cursor: 'pointer',
                        color: '#6b7280'
                    }}
                >
                    &times;
                </button>

                <h2 style={{ marginTop: 0, color: '#1f2937', fontSize: '1.5rem' }}>How to Chusmeate 🧐</h2>

                <div style={{ marginBottom: '20px' }}>
                    <h3 style={{ color: '#4b5563', fontSize: '1.1rem', borderBottom: '2px solid #e5e7eb', paddingBottom: '8px' }}>
                        🕵️ User Identity
                    </h3>
                    <p style={{ color: '#6b7280', fontSize: '0.95rem', lineHeight: '1.5' }}>
                        <strong>No signup required!</strong> Your identity is saved in this browser.
                        If you clear your cache or switch devices, you will lose the ability to edit or delete your posts.
                        <br /><br />
                        <em>Tip: Keep this browser safe if you want to maintain your reputation!</em>
                    </p>
                </div>

                <div style={{ marginBottom: '20px' }}>
                    <h3 style={{ color: '#4b5563', fontSize: '1.1rem', borderBottom: '2px solid #e5e7eb', paddingBottom: '8px' }}>
                        🎨 Legend & Meaning
                    </h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                            <span style={{ width: '16px', height: '16px', borderRadius: '50%', background: '#3b82f6' }}></span>
                            <span style={{ color: '#6b7280' }}><strong>Blue:</strong> Info, Neutral, Chill Vibes</span>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                            <span style={{ width: '16px', height: '16px', borderRadius: '50%', background: '#22c55e' }}></span>
                            <span style={{ color: '#6b7280' }}><strong>Green:</strong> Nature, Safe, Positive</span>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                            <span style={{ width: '16px', height: '16px', borderRadius: '50%', background: '#ef4444' }}></span>
                            <span style={{ color: '#6b7280' }}><strong>Red:</strong> Bustle, Chaos, Danger, Hotspots</span>
                        </div>
                    </div>
                </div>

                <div style={{ marginBottom: '20px' }}>
                    <h3 style={{ color: '#4b5563', fontSize: '1.1rem', borderBottom: '2px solid #e5e7eb', paddingBottom: '8px' }}>
                        👍 Impact of Votes
                    </h3>
                    <ul style={{ color: '#6b7280', fontSize: '0.95rem', paddingLeft: '20px', lineHeight: '1.5' }}>
                        <li style={{ marginBottom: '5px' }}><strong>Pins:</strong> Reach <span style={{ color: '#f59e0b', fontWeight: 'bold' }}>5 votes</span> to make the label permanently visible on the map!</li>
                        <li style={{ marginBottom: '5px' }}><strong>Areas:</strong> More votes = <strong>BIGGER</strong> text size.</li>

                    </ul>
                </div>

                <button
                    onClick={onClose}
                    style={{
                        width: '100%',
                        padding: '12px',
                        backgroundColor: '#4f46e5',
                        color: 'white',
                        border: 'none',
                        borderRadius: '8px',
                        fontWeight: 'bold',
                        cursor: 'pointer',
                        fontSize: '1rem',
                        marginTop: '10px'
                    }}
                >
                    Got it!
                </button>
            </div>
        </div>
    );
};

export default HelpModal;
