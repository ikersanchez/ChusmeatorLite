import React, { useEffect, useState } from 'react';
import logo from '../assets/logo.png';

const IntroScreen = ({ onComplete }) => {
    const [isVisible, setIsVisible] = useState(true);
    const [isFadingOut, setIsFadingOut] = useState(false);

    useEffect(() => {
        const timer = setTimeout(() => {
            setIsFadingOut(true);
            setTimeout(() => {
                setIsVisible(false);
                onComplete();
            }, 600); // Smooth fade out duration
        }, 2800);

        return () => clearTimeout(timer);
    }, [onComplete]);

    if (!isVisible) return null;

    return (
        <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            width: '100vw',
            height: '100dvh', // Use dvh for mobile support
            backgroundColor: '#0f172a', // Sleek dark theme
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999,
            opacity: isFadingOut ? 0 : 1,
            transition: 'opacity 0.6s cubic-bezier(0.4, 0, 0.2, 1)',
            fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
        }}>
            {/* Background dynamic orbs for depth */}
            <div style={{
                position: 'absolute',
                top: '15%',
                left: '20%',
                width: '40vw',
                height: '40vw',
                background: 'radial-gradient(circle, rgba(99,102,241,0.15) 0%, rgba(99,102,241,0) 70%)',
                filter: 'blur(40px)',
                animation: 'pulseBackground 4s ease-in-out infinite alternate',
                zIndex: 0
            }} />
            <div style={{
                position: 'absolute',
                bottom: '10%',
                right: '15%',
                width: '50vw',
                height: '50vw',
                background: 'radial-gradient(circle, rgba(236,72,153,0.1) 0%, rgba(236,72,153,0) 70%)',
                filter: 'blur(50px)',
                animation: 'pulseBackground 5s ease-in-out infinite alternate-reverse',
                zIndex: 0
            }} />

            <div style={{
                zIndex: 1,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                animation: 'slideUpFade 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards'
            }}>
                {/* Modern SVG Logo */}
                <div style={{
                    position: 'relative',
                    width: '120px',
                    height: '120px',
                    marginBottom: '2rem',
                    animation: 'floatIcon 3s ease-in-out infinite'
                }}>
                    <svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <defs>
                            <linearGradient id="glassGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                                <stop offset="0%" stopColor="rgba(255,255,255,0.4)" />
                                <stop offset="100%" stopColor="rgba(255,255,255,0.1)" />
                            </linearGradient>
                            <filter id="glassBlur">
                                <feGaussianBlur stdDeviation="2" />
                            </filter>
                        </defs>
                        
                        {/* Outer Glow */}
                        <circle cx="45" cy="45" r="30" fill="none" stroke="rgba(99,102,241,0.5)" strokeWidth="4" filter="blur(6px)" />
                        
                        {/* Glass Body */}
                        <circle cx="45" cy="45" r="30" fill="url(#glassGradient)" stroke="rgba(255,255,255,0.8)" strokeWidth="3" backdropFilter="blur(10px)" />
                        
                        {/* Inner reflection */}
                        <path d="M 25 35 A 25 25 0 0 1 55 20" stroke="rgba(255,255,255,0.6)" strokeWidth="3" strokeLinecap="round" fill="none" />
                        
                        {/* Handle */}
                        <path d="M 66 66 L 88 88" stroke="url(#glassGradient)" strokeWidth="12" strokeLinecap="round" />
                        <path d="M 66 66 L 88 88" stroke="rgba(255,255,255,0.8)" strokeWidth="4" strokeLinecap="round" />
                        
                        {/* Dynamic Eye/Center point */}
                        <circle cx="45" cy="45" r="8" fill="#e2e8f0">
                            <animate attributeName="r" values="6;9;6" dur="2s" repeatCount="indefinite" />
                            <animate attributeName="fill" values="#e2e8f0;#6366f1;#e2e8f0" dur="4s" repeatCount="indefinite" />
                        </circle>
                    </svg>
                </div>

                <h1 style={{
                    fontSize: 'clamp(2.5rem, 8vw, 4rem)',
                    fontWeight: '800',
                    color: '#ffffff',
                    margin: 0,
                    letterSpacing: '-0.04em',
                    background: 'linear-gradient(to right, #ffffff, #cbd5e1)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    textShadow: '0 4px 20px rgba(0,0,0,0.3)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                }}>
                    <img 
                        src={logo} 
                        alt="Logo" 
                        style={{ 
                            height: '1.8em', 
                            width: 'auto', 
                            objectFit: 'contain', 
                            filter: 'drop-shadow(0 4px 6px rgba(0,0,0,0.4))',
                            margin: '0 -0.8em' // Removes the transparent padding from the original image width
                        }} 
                    />
                    Chusmeator
                </h1>
                
                <p style={{
                    fontSize: 'clamp(1rem, 4vw, 1.25rem)',
                    color: '#94a3b8',
                    marginTop: '0.75rem',
                    fontWeight: '400',
                    letterSpacing: '0.02em',
                    opacity: 0,
                    animation: 'fadeIn 0.8s ease-out forwards 0.3s'
                }}>
                    Discover and share information on the map
                </p>
            </div>

            {/* Glassmorphism Warning Box */}
            <div style={{
                position: 'absolute',
                bottom: 'max(2rem, env(safe-area-inset-bottom, 2rem))',
                left: '50%',
                transform: 'translateX(-50%)',
                width: 'max-content',
                maxWidth: '92%',
                padding: '1rem 1.25rem',
                background: 'rgba(30, 41, 59, 0.4)',
                backdropFilter: 'blur(16px)',
                WebkitBackdropFilter: 'blur(16px)',
                borderRadius: '16px',
                border: '1px solid rgba(226, 232, 240, 0.1)',
                boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
                color: '#e2e8f0',
                fontSize: 'clamp(0.8rem, 3.5vw, 0.95rem)',
                fontWeight: '500',
                textAlign: 'left',
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                opacity: 0,
                animation: 'slideUpWarning 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards 0.6s'
            }}>
                <span style={{ fontSize: '1.25rem', flexShrink: 0 }}>⚠️</span>
                <span style={{ lineHeight: '1.4' }}>
                    Toxic comments, sensitive information, and personal data are strictly prohibited.
                </span>
            </div>

            <style>{`
                @keyframes floatIcon {
                    0%, 100% { transform: translateY(0px) rotate(0deg); }
                    50% { transform: translateY(-12px) rotate(2deg); filter: drop-shadow(0 10px 20px rgba(99,102,241,0.3)); }
                }
                @keyframes slideUpFade {
                    0% { transform: translateY(30px); opacity: 0; filter: blur(4px); }
                    100% { transform: translateY(0); opacity: 1; filter: blur(0); }
                }
                @keyframes slideUpWarning {
                    0% { transform: translate(-50%, 20px); opacity: 0; }
                    100% { transform: translate(-50%, 0); opacity: 1; }
                }
                @keyframes pulseBackground {
                    0% { transform: scale(1); opacity: 0.5; }
                    100% { transform: scale(1.1); opacity: 0.8; }
                }
                @keyframes fadeIn {
                    to { opacity: 1; }
                }
            `}</style>
        </div>
    );
};

export default IntroScreen;
