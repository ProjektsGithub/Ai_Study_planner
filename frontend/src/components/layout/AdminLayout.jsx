import { useState, useEffect } from 'react';
import { Layout, Menu, Button, Avatar, Dropdown, Space, Typography, Modal, Tooltip } from 'antd';
import { Link, useLocation, useNavigate, Outlet } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import GlobalSearch from '../GlobalSearch';
import {
  DashboardOutlined,
  BankOutlined,
  BookOutlined,
  BranchesOutlined,
  CalendarOutlined,
  ReadOutlined,
  ImportOutlined,
  HistoryOutlined,
  UsergroupAddOutlined,
  SettingOutlined,
  HomeOutlined,
  LogoutOutlined,
  MenuUnfoldOutlined,
  MenuFoldOutlined,
  UserOutlined,
  AppstoreOutlined,
  SafetyCertificateOutlined,
  BarChartOutlined,
  QuestionCircleOutlined,
} from '@ant-design/icons';

const { Header, Sider, Content } = Layout;
const { Text, Paragraph } = Typography;

const AdminLayout = () => {
  const [collapsed, setCollapsed] = useState(false);
  const [helpOpen, setHelpOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout, hasRole } = useAuth();
  const { lang, changeLanguage, t } = useLanguage();

  const isSuperAdmin = hasRole('super_admin');

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.altKey) {
        switch (e.key.toLowerCase()) {
          case 'd':
            e.preventDefault();
            navigate('/admin/dashboard');
            break;
          case 'u':
            e.preventDefault();
            navigate('/admin/universities');
            break;
          case 'p':
            e.preventDefault();
            navigate('/admin/programs');
            break;
          case 't':
            e.preventDefault();
            navigate('/admin/tracks');
            break;
          case 'k':
            e.preventDefault();
            navigate('/admin/semesters');
            break;
          case 'e':
            e.preventDefault();
            navigate('/admin/teaching-units');
            break;
          case 'o':
            e.preventDefault();
            navigate('/admin/courses');
            break;
          case 's': {
            e.preventDefault();
            const input = document.querySelector('.ant-input-affix-wrapper input, input[placeholder*="Search"]');
            if (input) {
              input.focus();
              input.select();
            }
            break;
          }
          case 'n': {
            e.preventDefault();
            const addBtn = document.querySelector('button.ant-btn-primary');
            if (addBtn) {
              addBtn.click();
            }
            break;
          }
          case 'r': {
            e.preventDefault();
            const reloadBtn = document.querySelector('button:has(.anticon-reload), button.ant-btn:has(span:contains("Reload")), button.ant-btn:has(span:contains("Reset"))');
            if (reloadBtn) {
              reloadBtn.click();
            }
            break;
          }
          case 'c': {
            e.preventDefault();
            const closeBtn = document.querySelector('.ant-modal-close, .ant-modal-footer button:not(.ant-btn-primary), .ant-drawer-close');
            if (closeBtn) {
              closeBtn.click();
            }
            break;
          }
          case 'h': {
            e.preventDefault();
            setHelpOpen((prev) => !prev);
            break;
          }
          default:
            break;
        }
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [navigate]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // Define sidebar items
  const menuItems = [
    {
      key: '/admin/dashboard',
      icon: <DashboardOutlined />,
      label: <Link to="/admin/dashboard">{t('nav.dashboard')}</Link>,
    },
    {
      key: '/admin/universities',
      icon: <BankOutlined />,
      label: <Link to="/admin/universities">{t('nav.universities')}</Link>,
    },
    {
      key: '/admin/programs',
      icon: <BookOutlined />,
      label: <Link to="/admin/programs">{t('nav.programs')}</Link>,
    },
    {
      key: '/admin/tracks',
      icon: <BranchesOutlined />,
      label: <Link to="/admin/tracks">{t('nav.tracks')}</Link>,
    },
    {
      key: '/admin/rules',
      icon: <SafetyCertificateOutlined />,
      label: <Link to="/admin/rules">{t('nav.rules')}</Link>,
    },
    {
      key: '/admin/semesters',
      icon: <CalendarOutlined />,
      label: <Link to="/admin/semesters">{t('nav.semesters')}</Link>,
    },
    {
      key: '/admin/teaching-units',
      icon: <AppstoreOutlined />,
      label: <Link to="/admin/teaching-units">{t('nav.units')}</Link>,
    },
    {
      key: '/admin/courses',
      icon: <ReadOutlined />,
      label: <Link to="/admin/courses">{t('nav.courses')}</Link>,
    },
    {
      key: '/admin/imports',
      icon: <ImportOutlined />,
      label: <Link to="/admin/imports">{t('nav.imports')}</Link>,
    },
    {
      key: '/admin/reports',
      icon: <BarChartOutlined />,
      label: <Link to="/admin/reports">{t('nav.reports')}</Link>,
    },
  ];

  // Add Super Admin-only sections
  if (isSuperAdmin) {
    menuItems.push(
      {
        type: 'divider',
      },
      {
        key: '/admin/audit',
        icon: <HistoryOutlined />,
        label: <Link to="/admin/audit">{t('nav.audit')}</Link>,
      },
      {
        key: '/admin/roles',
        icon: <UsergroupAddOutlined />,
        label: <Link to="/admin/roles">{t('nav.roles')}</Link>,
      },
      {
        key: '/admin/settings',
        icon: <SettingOutlined />,
        label: <Link to="/admin/settings">{t('nav.settings')}</Link>,
      }
    );
  }

  // Common footer portal links
  menuItems.push(
    {
      type: 'divider',
    },
    {
      key: '/dashboard',
      icon: <HomeOutlined />,
      label: <Link to="/dashboard">{t('nav.student_portal')}</Link>,
    }
  );

  const userMenu = {
    items: [
      {
        key: 'profile',
        icon: <UserOutlined />,
        label: <Link to="/profile">{t('nav.my_profile')}</Link>,
      },
      {
        type: 'divider',
      },
      {
        key: 'language',
        label: lang === 'de' ? 'Sprache: Deutsch' : 'Language: English',
        children: [
          {
            key: 'lang-de',
            label: 'Deutsch',
            disabled: lang === 'de',
            onClick: () => changeLanguage('de'),
          },
          {
            key: 'lang-en',
            label: 'English',
            disabled: lang === 'en',
            onClick: () => changeLanguage('en'),
          },
        ]
      },
      {
        type: 'divider',
      },
      {
        key: 'logout',
        icon: <LogoutOutlined />,
        label: t('nav.logout'),
        danger: true,
        onClick: handleLogout,
      },
    ],
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        breakpoint="lg"
        collapsedWidth={0}
        onCollapse={(value) => setCollapsed(value)}
        theme="dark"
        width={250}
        style={{
          boxShadow: '2px 0 8px 0 rgba(29,35,41,.05)',
          position: 'sticky',
          top: 0,
          height: '100vh',
          zIndex: 10,
        }}
      >
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: collapsed ? 'center' : 'flex-start',
            padding: '0 24px',
            background: '#002140',
            transition: 'all 0.2s',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div
              style={{
                width: 32,
                height: 32,
                borderRadius: 8,
                background: 'linear-gradient(135deg, #1890ff 0%, #096dd9 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#fff',
                fontWeight: 'bold',
                fontSize: 16,
              }}
            >
              A
            </div>
            {!collapsed && (
              <span
                style={{
                  color: '#fff',
                  fontWeight: 600,
                  fontSize: 15,
                  letterSpacing: '0.5px',
                  whiteSpace: 'nowrap',
                }}
              >
                Study Planner Admin
              </span>
            )}
          </div>
        </div>

        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          style={{ borderRight: 0, marginTop: 16 }}
        />
      </Sider>

      <Layout style={{ background: '#f5f7fa' }}>
        <Header
          style={{
            padding: '0 24px',
            background: '#fff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            boxShadow: '0 1px 4px rgba(0,21,41,.08)',
            position: 'sticky',
            top: 0,
            zIndex: 9,
            height: 64,
          }}
        >
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
            style={{ fontSize: '16px', width: 64, height: 64 }}
          />

          <div style={{ flex: 1, margin: '0 24px', maxWidth: 450 }}>
            <GlobalSearch />
          </div>

          <Space size={24}>
            <Tooltip title={t('shortcut.legend') + ' (Alt + H)'}>
              <Button
                type="text"
                icon={<QuestionCircleOutlined />}
                onClick={() => setHelpOpen(true)}
                style={{ fontSize: '18px', color: '#8c8c8c', display: 'flex', alignItems: 'center', justifyContent: 'center', width: 32, height: 32 }}
              />
            </Tooltip>
            {user && (
              <Dropdown menu={userMenu} placement="bottomRight" trigger={['click']}>
                <Space style={{ cursor: 'pointer' }}>
                  <Avatar style={{ backgroundColor: '#1890ff' }} icon={<UserOutlined />} />
                  <div style={{ display: 'flex', flexDirection: 'column', lineHeight: '1.2' }} className="hidden sm:flex">
                    <Text strong style={{ fontSize: 13 }}>{user.name}</Text>
                    <Text type="secondary" style={{ fontSize: 11 }}>
                      {isSuperAdmin ? 'Super Admin' : 'Admin'}
                    </Text>
                  </div>
                </Space>
              </Dropdown>
            )}
          </Space>
        </Header>

        <Content
          style={{
            margin: '24px 24px 0',
            minHeight: 280,
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <div style={{ flex: 1 }}>
            <Outlet />
          </div>
        </Content>
      </Layout>

      {/* Keyboard Shortcuts Help Modal */}
      <Modal
        title={
          <Space>
            <QuestionCircleOutlined style={{ color: '#1890ff' }} />
            <span>{t('shortcut.legend')}</span>
          </Space>
        }
        open={helpOpen}
        onCancel={() => setHelpOpen(false)}
        footer={[
          <Button key="close" type="primary" onClick={() => setHelpOpen(false)}>
            {lang === 'de' ? 'Verstanden' : 'Got it'}
          </Button>
        ]}
        width={450}
        destroyOnClose
      >
        <div style={{ padding: '8px 0' }}>
          <Paragraph>
            Use the following global administrative keyboard shortcuts for quick keyboard-driven navigation:
          </Paragraph>
          <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '12px 24px', alignItems: 'center' }}>
            <Text code>Alt + D</Text> <Text>Navigate to Dashboard</Text>
            <Text code>Alt + U</Text> <Text>Navigate to Universities</Text>
            <Text code>Alt + P</Text> <Text>Navigate to Study Programs</Text>
            <Text code>Alt + T</Text> <Text>Navigate to Academic Tracks</Text>
            <Text code>Alt + K</Text> <Text>Navigate to Semesters</Text>
            <Text code>Alt + E</Text> <Text>Navigate to Teaching Units</Text>
            <Text code>Alt + O</Text> <Text>Navigate to Courses</Text>
            <Text code>Alt + S</Text> <Text>Focus search input</Text>
            <Text code>Alt + N</Text> <Text>Add new entity (clicks Primary button)</Text>
            <Text code>Alt + R</Text> <Text>Refresh/Reload current data list</Text>
            <Text code>Alt + C</Text> <Text>Cancel or close current active modal</Text>
            <Text code>Alt + H</Text> <Text>Toggle this shortcuts legend dialog</Text>
          </div>
        </div>
      </Modal>
    </Layout>
  );
};

export default AdminLayout;
