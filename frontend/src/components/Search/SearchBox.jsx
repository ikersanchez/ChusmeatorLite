import React, { useState, useEffect, useRef } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';
import { api } from '../../api/apiService';
import { useDebounce } from '../../hooks/useDebounce';

const SearchBox = () => {
    const map = useMap();
    const [query, setQuery] = useState('');
    const [suggestions, setSuggestions] = useState([]);
    const [isSearching, setIsSearching] = useState(false);
    const [showSuggestions, setShowSuggestions] = useState(false);
    const containerRef = useRef(null);

    useEffect(() => {
        if (containerRef.current) {
            L.DomEvent.disableClickPropagation(containerRef.current);
            L.DomEvent.disableScrollPropagation(containerRef.current);
        }
    }, []);

    const debouncedQuery = useDebounce(query, 300);

    useEffect(() => {
        const fetchSuggestions = async () => {
            if (debouncedQuery.length > 2) {
                setIsSearching(true);
                try {
                    const results = await api.searchAddress(debouncedQuery);
                    setSuggestions(results);
                    setShowSuggestions(true);
                } catch (err) {
                    console.error("Search error:", err);
                } finally {
                    setIsSearching(false);
                }
            } else {
                setSuggestions([]);
                setShowSuggestions(false);
            }
        };

        fetchSuggestions();
    }, [debouncedQuery]);

    const handleSelect = (result) => {
        const { lat, lon, display_name } = result;
        map.flyTo([lat, lon], 16);
        setQuery(display_name);
        setSuggestions([]);
        setShowSuggestions(false);
    };

    const handleSearch = async (e) => {
        e.preventDefault();
        if (!query) return;

        if (suggestions.length > 0) {
            handleSelect(suggestions[0]);
        } else {
            setIsSearching(true);
            try {
                const locations = await api.searchAddress(query);
                if (locations.length > 0) {
                    handleSelect(locations[0]);
                }
            } catch (err) {
                console.error(err);
            } finally {
                setIsSearching(false);
            }
        }
    };

    return (
        <div className="search-box-container" ref={containerRef} style={{
            position: 'absolute',
            top: '10px',
            left: '10px',
            right: '10px',
            zIndex: 1000,
            maxWidth: '420px',
            pointerEvents: 'none',
        }}>
            <div className="search-input-wrapper" style={{
                background: 'rgba(255, 255, 255, 0.88)',
                backdropFilter: 'blur(12px) saturate(180%)',
                WebkitBackdropFilter: 'blur(12px) saturate(180%)',
                padding: '8px',
                borderRadius: '14px',
                boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
                border: '1px solid rgba(0,0,0,0.06)',
                display: 'flex',
                gap: '6px',
                pointerEvents: 'auto',
            }}>
                <form onSubmit={handleSearch} style={{ display: 'flex', gap: '6px', flex: 1 }}>
                    <input
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        onFocus={() => { if (suggestions.length > 0) setShowSuggestions(true); }}
                        onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
                        placeholder="Search address..."
                        style={{
                            flex: 1,
                            padding: '10px 12px',
                            borderRadius: '10px',
                            border: '1px solid rgba(0,0,0,0.08)',
                            fontSize: '16px',
                            background: 'rgba(255,255,255,0.7)',
                            outline: 'none',
                            minWidth: 0,
                        }}
                    />
                    <button
                        type="submit"
                        disabled={isSearching}
                        style={{
                            padding: '10px 16px',
                            background: 'var(--accent)',
                            color: 'white',
                            border: 'none',
                            borderRadius: '10px',
                            cursor: 'pointer',
                            fontWeight: 'bold',
                            fontSize: '14px',
                            whiteSpace: 'nowrap',
                            flexShrink: 0,
                        }}
                    >
                        {isSearching ? '...' : '🔍'}
                    </button>
                </form>
            </div>

            {showSuggestions && suggestions.length > 0 && (
                <div className="search-suggestions" style={{
                    background: 'rgba(255,255,255,0.95)',
                    backdropFilter: 'blur(12px)',
                    WebkitBackdropFilter: 'blur(12px)',
                    borderRadius: '12px',
                    boxShadow: '0 8px 32px rgba(0,0,0,0.12)',
                    maxHeight: '250px',
                    overflowY: 'auto',
                    marginTop: '6px',
                    pointerEvents: 'auto',
                    border: '1px solid rgba(0,0,0,0.06)',
                }}>
                    {suggestions.map((result, index) => (
                        <div
                            key={index}
                            onMouseDown={(e) => {
                                e.preventDefault();
                                handleSelect(result);
                            }}
                            className="suggestion-item"
                            style={{
                                padding: '10px 12px',
                                borderBottom: index < suggestions.length - 1 ? '1px solid rgba(0,0,0,0.05)' : 'none',
                                cursor: 'pointer',
                                fontSize: '14px',
                                color: 'var(--text)',
                                transition: 'background 0.15s',
                            }}
                            onMouseEnter={(e) => e.target.style.background = 'rgba(59, 130, 246, 0.06)'}
                            onMouseLeave={(e) => e.target.style.background = 'transparent'}
                        >
                            {result.display_name}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default SearchBox;
