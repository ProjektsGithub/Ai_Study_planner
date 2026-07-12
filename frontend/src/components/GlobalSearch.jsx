import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Input, Spin, Card, Typography, Empty, Space } from 'antd';
import {
  SearchOutlined,
  BankOutlined,
  EnvironmentOutlined,
  BookOutlined,
  BranchesOutlined,
  CalendarOutlined,
  AppstoreOutlined,
  ReadOutlined,
} from '@ant-design/icons';
import apiClient from '../api/client';

const { Text } = Typography;

const escapeRegExp = (string) => {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
};

const highlightText = (text, query) => {
  if (!query || !text) return text;
  const parts = text.split(new RegExp(`(${escapeRegExp(query)})`, 'gi'));
  return (
    <span>
      {parts.map((part, index) =>
        part.toLowerCase() === query.toLowerCase() ? (
          <mark key={index} style={{ backgroundColor: '#fff566', padding: 0 }}>
            {part}
          </mark>
        ) : (
          part
        )
      )}
    </span>
  );
};

const GlobalSearch = () => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [isOpen, setIsOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const containerRef = useRef(null);
  const navigate = useNavigate();

  // Click outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Debounced API query call
  useEffect(() => {
    if (query.trim().length < 2) {
      setResults(null);
      setLoading(false);
      setActiveIndex(-1);
      return;
    }

    setLoading(true);
    const delayDebounce = setTimeout(async () => {
      try {
        const response = await apiClient.get('/api/v1/admin/search', {
          params: { q: query.trim() },
        });
        setResults(response.data);
        setActiveIndex(-1);
      } catch (err) {
        console.error('Global search error:', err);
      } finally {
        setLoading(false);
      }
    }, 300);

    return () => clearTimeout(delayDebounce);
  }, [query]);

  const handleSelect = (entityType) => {
    setIsOpen(false);
    setQuery('');
    setResults(null);
    setActiveIndex(-1);

    // Map entity types to routes
    const routes = {
      universities: '/admin/universities',
      campuses: '/admin/universities',
      programs: '/admin/programs',
      tracks: '/admin/tracks',
      semesters: '/admin/semesters',
      teaching_units: '/admin/teaching-units',
      courses: '/admin/courses',
    };

    const targetRoute = routes[entityType] || '/admin/dashboard';
    navigate(targetRoute);
  };

  const getEntityIcon = (type) => {
    switch (type) {
      case 'universities':
        return <BankOutlined style={{ color: '#1890ff' }} />;
      case 'campuses':
        return <EnvironmentOutlined style={{ color: '#52c41a' }} />;
      case 'programs':
        return <BookOutlined style={{ color: '#722ed1' }} />;
      case 'tracks':
        return <BranchesOutlined style={{ color: '#fa8c16' }} />;
      case 'semesters':
        return <CalendarOutlined style={{ color: '#eb2f96' }} />;
      case 'teaching_units':
        return <AppstoreOutlined style={{ color: '#13c2c2' }} />;
      case 'courses':
        return <ReadOutlined style={{ color: '#f5222d' }} />;
      default:
        return <SearchOutlined />;
    }
  };

  const getEntityTypeName = (type) => {
    switch (type) {
      case 'universities':
        return 'Universities';
      case 'campuses':
        return 'Campuses';
      case 'programs':
        return 'Study Programs';
      case 'tracks':
        return 'Academic Tracks';
      case 'semesters':
        return 'Semesters';
      case 'teaching_units':
        return 'Teaching Units';
      case 'courses':
        return 'Courses';
      default:
        return type.toUpperCase();
    }
  };

  // Flatten results helper
  const getFlatResults = () => {
    if (!results || !results.results_by_type) return [];
    const list = [];
    Object.entries(results.results_by_type).forEach(([type, items]) => {
      if (items && items.length > 0) {
        items.forEach((item) => {
          list.push({ ...item, type });
        });
      }
    });
    return list;
  };

  const flatResults = getFlatResults();

  const handleKeyDown = (e) => {
    if (!isOpen || flatResults.length === 0) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex((prev) => (prev + 1) % flatResults.length);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex((prev) => (prev - 1 + flatResults.length) % flatResults.length);
    } else if (e.key === 'Enter') {
      if (activeIndex >= 0 && activeIndex < flatResults.length) {
        e.preventDefault();
        const selected = flatResults[activeIndex];
        handleSelect(selected.type);
      }
    } else if (e.key === 'Escape') {
      e.preventDefault();
      setIsOpen(false);
    }
  };

  const renderDropdownContent = () => {
    if (loading) {
      return (
        <div style={{ padding: '24px', textAlign: 'center' }}>
          <Spin size="default" tip="Searching curriculum..." />
        </div>
      );
    }

    if (!results || results.total_hits === 0) {
      return (
        <div style={{ padding: '16px' }}>
          <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No curriculum entities match query." />
        </div>
      );
    }

    const { results_by_type, total_hits, search_duration_ms } = results;

    return (
      <div style={{ maxHeight: '420px', overflowY: 'auto' }}>
        {Object.entries(results_by_type).map(([type, items]) => {
          if (!items || items.length === 0) return null;

          return (
            <div key={type} style={{ borderBottom: '1px solid #f0f0f0' }}>
              <div style={{ padding: '8px 16px', background: '#fafafa', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Text type="secondary" strong style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  {getEntityTypeName(type)}
                </Text>
                <Text type="secondary" style={{ fontSize: '10px' }}>
                  {items.length} matched
                </Text>
              </div>

              {items.map((item) => {
                // Find index of this item in the flat array
                const itemIndex = flatResults.findIndex((r) => r.id === item.id && r.type === type);
                const isItemFocused = itemIndex === activeIndex;

                return (
                  <div
                    key={item.id}
                    onClick={() => handleSelect(type)}
                    style={{
                      padding: '10px 16px',
                      cursor: 'pointer',
                      display: 'flex',
                      flexDirection: 'column',
                      transition: 'background 0.2s',
                      backgroundColor: isItemFocused ? '#e6f7ff' : 'transparent',
                    }}
                    onMouseEnter={(e) => {
                      if (!isItemFocused) {
                        e.currentTarget.style.backgroundColor = '#f5f7fa';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (!isItemFocused) {
                        e.currentTarget.style.backgroundColor = 'transparent';
                      }
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '2px' }}>
                      {getEntityIcon(type)}
                      <span style={{ fontWeight: 500, fontSize: '13px', color: '#262626' }}>
                        {item.code && (
                          <span style={{ color: '#595959', marginRight: '6px', fontSize: '12px', background: '#f0f0f0', padding: '1px 4px', borderRadius: '3px' }}>
                            {highlightText(item.code, query)}
                          </span>
                        )}
                        {highlightText(item.name, query)}
                      </span>
                      {item.name_de && (
                        <span style={{ fontSize: '11px', color: '#8c8c8c' }}>
                          (DE: {highlightText(item.name_de, query)})
                        </span>
                      )}
                    </div>
                    {item.description && (
                      <Text type="secondary" style={{ fontSize: '12px', paddingLeft: '22px' }} ellipsis>
                        {highlightText(item.description, query)}
                      </Text>
                    )}
                  </div>
                );
              })}
            </div>
          );
        })}

        <div
          style={{
            padding: '8px 16px',
            background: '#fafafa',
            borderTop: '1px solid #f0f0f0',
            textAlign: 'right',
            fontSize: '11px',
            color: '#8c8c8c',
          }}
        >
          Found {total_hits} results in <span style={{ fontWeight: 600, color: '#595959' }}>{search_duration_ms} ms</span>
        </div>
      </div>
    );
  };

  return (
    <div ref={containerRef} style={{ position: 'relative', width: '100%', zIndex: 1050 }}>
      <Input
        placeholder="Type to search curriculum (e.g. course, track, program)..."
        prefix={<SearchOutlined style={{ color: '#bfbfbf', marginRight: '4px' }} />}
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
          setIsOpen(true);
        }}
        onFocus={() => setIsOpen(true)}
        onKeyDown={handleKeyDown}
        allowClear
        style={{
          borderRadius: '20px',
          padding: '6px 16px',
          boxShadow: 'inset 0 1px 2px rgba(0,0,0,0.05)',
          border: '1px solid #d9d9d9',
          transition: 'all 0.3s',
        }}
      />

      {isOpen && query.trim().length >= 2 && (
        <Card
          bodyStyle={{ padding: 0 }}
          style={{
            position: 'absolute',
            top: 'calc(100% + 8px)',
            left: 0,
            right: 0,
            boxShadow: '0 6px 16px -8px rgba(0, 0, 0, 0.08), 0 9px 28px 0 rgba(0, 0, 0, 0.05), 0 12px 48px 16px rgba(0, 0, 0, 0.03)',
            borderRadius: '8px',
            border: '1px solid #f0f0f0',
            overflow: 'hidden',
            background: '#ffffff',
          }}
        >
          {renderDropdownContent()}
        </Card>
      )}
    </div>
  );
};

export default GlobalSearch;
