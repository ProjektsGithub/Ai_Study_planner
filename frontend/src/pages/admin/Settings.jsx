import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate, useBlocker, Link } from 'react-router-dom';
import apiClient from '../../api/client';
import {
  Button,
  Form,
  Input,
  InputNumber,
  Select,
  Card,
  Typography,
  Breadcrumb,
  Tabs,
  Space,
  Row,
  Col,
  Result,
  Popconfirm,
  Modal,
  message,
} from 'antd';
import {
  SettingOutlined,
  SaveOutlined,
  ReloadOutlined,
  SafetyCertificateOutlined,
  FileTextOutlined,
  CalendarOutlined,
  WarningOutlined,
} from '@ant-design/icons';
import { useAuth } from '../../context/AuthContext';

const { Title, Paragraph, Text } = Typography;
const { Option } = Select;

const Settings = () => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { hasRole } = useAuth();
  const isSuperAdmin = hasRole('super_admin');
  const [form] = Form.useForm();
  const [activeTab, setActiveTab] = useState('ects');

  // Dirty form state
  const [isFormDirty, setIsFormDirty] = useState(false);

  const blocker = useBlocker(
    ({ currentValue, nextLocation }) =>
      isFormDirty && currentValue.pathname !== nextLocation.pathname
  );

  // 1. Fetch system settings
  const {
    data: settingsData,
    isLoading: isSettingsLoading,
    refetch: refetchSettings,
  } = useQuery({
    queryKey: ['adminSystemSettings'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/admin/settings');
      return response.data;
    },
    enabled: isSuperAdmin,
  });

  // Populate form fields when settings fetch returns
  useEffect(() => {
    if (settingsData?.settings) {
      const initialValues = {};
      settingsData.settings.forEach((s) => {
        // Parse numbers if they should be integer inputs
        const intKeys = [
          'default_ects_per_semester',
          'default_total_ects_bachelor',
          'default_total_ects_master',
          'default_total_ects_doctorate',
          'min_ects_per_course',
          'max_ects_per_course',
          'max_login_attempts',
          'account_lockout_minutes',
          'min_password_length',
          'session_timeout_hours',
          'max_import_file_size_mb',
          'max_export_rows',
        ];

        if (intKeys.includes(s.key)) {
          initialValues[s.key] = parseInt(s.value, 10);
        } else {
          initialValues[s.key] = s.value;
        }
      });
      form.setFieldsValue(initialValues);
      setIsFormDirty(false);
    }
  }, [settingsData, form]);

  // 2. Mutations
  const updateSettingsMutation = useMutation({
    mutationFn: async (payload) => {
      const response = await apiClient.put('/api/v1/admin/settings', payload);
      return response.data;
    },
    onSuccess: () => {
      message.success('System settings saved successfully.');
      setIsFormDirty(false);
      queryClient.invalidateQueries({ queryKey: ['adminSystemSettings'] });
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || 'Failed to save system settings.');
    },
  });

  const resetSettingsMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post('/api/v1/admin/settings/reset');
      return response.data;
    },
    onSuccess: () => {
      message.success('System settings reset to default parameters.');
      setIsFormDirty(false);
      queryClient.invalidateQueries({ queryKey: ['adminSystemSettings'] });
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || 'Failed to reset settings.');
    },
  });

  // Access check guard
  if (!isSuperAdmin) {
    return (
      <div style={{ padding: 24 }}>
        <Card style={{ borderRadius: 8, boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
          <Result
            status="403"
            title="403 Access Denied"
            subTitle="Sorry, only Super Administrators are authorized to view and modify system configuration parameters."
            extra={
              <Button type="primary" onClick={() => navigate('/admin/dashboard')}>
                Return to Dashboard
              </Button>
            }
          />
        </Card>
      </div>
    );
  }

  const handleFinish = (values) => {
    // Map values back to strings for payload
    const updates = {};
    Object.entries(values).forEach(([key, val]) => {
      if (val !== undefined && val !== null) {
        updates[key] = String(val);
      }
    });

    updateSettingsMutation.mutate({ updates });
  };

  const settingsMap = {};
  settingsData?.settings?.forEach((s) => {
    settingsMap[s.key] = s;
  });

  const renderSettingMeta = (key) => {
    const s = settingsMap[key];
    if (!s || (!s.updated_at && !s.updated_by)) return null;
    return (
      <div style={{ fontSize: '11px', color: '#8c8c8c', marginTop: '4px' }}>
        Last updated {s.updated_at ? new Date(s.updated_at).toLocaleString() : ''}
        {s.updated_by ? ` by ${s.updated_by}` : ''}
      </div>
    );
  };

  const tabItems = [
    {
      key: 'ects',
      label: (
        <span>
          <CalendarOutlined /> ECTS Rules
        </span>
      ),
      children: (
        <div style={{ padding: '8px' }}>
          <Title level={4} style={{ marginBottom: 16 }}>ECTS & Credits Allocations</Title>
          <Row gutter={24}>
            <Col xs={24} md={12}>
              <Form.Item
                name="default_ects_per_semester"
                label="Default ECTS Credits per Semester"
                extra={renderSettingMeta('default_ects_per_semester')}
                rules={[{ required: true, message: 'Required' }]}
              >
                <InputNumber min={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item
                name="min_ects_per_course"
                label="Minimum ECTS Credits per Course"
                extra={renderSettingMeta('min_ects_per_course')}
                rules={[{ required: true, message: 'Required' }]}
              >
                <InputNumber min={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item
                name="max_ects_per_course"
                label="Maximum ECTS Credits per Course"
                extra={renderSettingMeta('max_ects_per_course')}
                rules={[{ required: true, message: 'Required' }]}
              >
                <InputNumber min={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Title level={5} style={{ marginTop: 24, marginBottom: 16 }}>Degree Graduation Milestones</Title>
          <Row gutter={24}>
            <Col xs={24} md={8}>
              <Form.Item
                name="default_total_ects_bachelor"
                label="Bachelor's Target (ECTS)"
                extra={renderSettingMeta('default_total_ects_bachelor')}
                rules={[{ required: true, message: 'Required' }]}
              >
                <InputNumber min={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item
                name="default_total_ects_master"
                label="Master's Target (ECTS)"
                extra={renderSettingMeta('default_total_ects_master')}
                rules={[{ required: true, message: 'Required' }]}
              >
                <InputNumber min={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item
                name="default_total_ects_doctorate"
                label="Doctorate Target (ECTS)"
                extra={renderSettingMeta('default_total_ects_doctorate')}
                rules={[{ required: true, message: 'Required' }]}
              >
                <InputNumber min={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
        </div>
      ),
    },
    {
      key: 'security',
      label: (
        <span>
          <SafetyCertificateOutlined /> Security & Lockouts
        </span>
      ),
      children: (
        <div style={{ padding: '8px' }}>
          <Title level={4} style={{ marginBottom: 16 }}>Security Configuration & Policies</Title>
          <Row gutter={24}>
            <Col xs={24} md={12}>
              <Form.Item
                name="max_login_attempts"
                label="Max Login Attempts before Account Lockout"
                extra={renderSettingMeta('max_login_attempts')}
                rules={[{ required: true, message: 'Required' }]}
              >
                <InputNumber min={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item
                name="account_lockout_minutes"
                label="Account Lockout Duration (Minutes)"
                extra={renderSettingMeta('account_lockout_minutes')}
                rules={[{ required: true, message: 'Required' }]}
              >
                <InputNumber min={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item
                name="session_timeout_hours"
                label="Session Login Timeout (Hours)"
                extra={renderSettingMeta('session_timeout_hours')}
                rules={[{ required: true, message: 'Required' }]}
              >
                <InputNumber min={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item
                name="min_password_length"
                label="Minimum Password Length Policy"
                extra={renderSettingMeta('min_password_length')}
                rules={[{ required: true, message: 'Required' }]}
              >
                <InputNumber min={4} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item
                name="require_uppercase"
                label="Require Uppercase Letter in Passwords"
                extra={renderSettingMeta('require_uppercase')}
                rules={[{ required: true, message: 'Required' }]}
              >
                <Select>
                  <Option value="true">Yes, Enforce</Option>
                  <Option value="false">No, Optional</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item
                name="require_special_character"
                label="Require Special Character in Passwords"
                extra={renderSettingMeta('require_special_character')}
                rules={[{ required: true, message: 'Required' }]}
              >
                <Select>
                  <Option value="true">Yes, Enforce</Option>
                  <Option value="false">No, Optional</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
        </div>
      ),
    },
    {
      key: 'files',
      label: (
        <span>
          <FileTextOutlined /> File & Data Limits
        </span>
      ),
      children: (
        <div style={{ padding: '8px' }}>
          <Title level={4} style={{ marginBottom: 16 }}>File Management & Exports</Title>
          <Row gutter={24}>
            <Col xs={24} md={12}>
              <Form.Item
                name="max_import_file_size_mb"
                label="Max Excel Import Size (MB)"
                extra={renderSettingMeta('max_import_file_size_mb')}
                rules={[{ required: true, message: 'Required' }]}
              >
                <InputNumber min={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item
                name="max_export_rows"
                label="Max Data Rows in Report Exports"
                extra={renderSettingMeta('max_export_rows')}
                rules={[{ required: true, message: 'Required' }]}
              >
                <InputNumber min={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col xs={24} md={24}>
              <Form.Item
                name="allowed_import_formats"
                label="Allowed Import spreadsheet extensions (Comma-separated)"
                extra={renderSettingMeta('allowed_import_formats')}
                rules={[{ required: true, message: 'Required' }]}
              >
                <Input />
              </Form.Item>
            </Col>
          </Row>
        </div>
      ),
    },
    {
      key: 'general',
      label: (
        <span>
          <SettingOutlined /> General Configuration
        </span>
      ),
      children: (
        <div style={{ padding: '8px' }}>
          <Title level={4} style={{ marginBottom: 16 }}>Branding & System Configuration</Title>
          <Row gutter={24}>
            <Col xs={24} md={12}>
              <Form.Item
                name="platform_name"
                label="Platform Brand Display Name"
                extra={renderSettingMeta('platform_name')}
                rules={[{ required: true, message: 'Required' }]}
              >
                <Input />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item
                name="support_email"
                label="System Support Email Address"
                extra={renderSettingMeta('support_email')}
                rules={[
                  { required: true, message: 'Required' },
                  { type: 'email', message: 'Please enter a valid email address' },
                ]}
              >
                <Input />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item
                name="maintenance_mode"
                label="Maintenance Banner Offline Mode"
                extra={renderSettingMeta('maintenance_mode')}
                rules={[{ required: true, message: 'Required' }]}
              >
                <Select>
                  <Option value="true">Enable Offline Maintenance Banner</Option>
                  <Option value="false">Disable Maintenance Offline Mode</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
        </div>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px', background: '#fff', borderRadius: 8, minHeight: '100%' }}>
      {/* Header section */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16, marginBottom: 24 }}>
        <div>
          <Breadcrumb style={{ marginBottom: 8 }}>
            <Breadcrumb.Item><Link to="/admin/dashboard">Admin Platform</Link></Breadcrumb.Item>
            <Breadcrumb.Item>System Settings</Breadcrumb.Item>
          </Breadcrumb>
          <Title level={2} style={{ margin: 0 }}>System Controls & Configurations</Title>
          <Paragraph style={{ margin: 0, marginTop: 4 }}>
            Customize curriculum credit benchmarks, database security constraints, spreadsheet size checks, and branding options.
          </Paragraph>
        </div>

        <Space>
          <Popconfirm
            title="Reset Settings?"
            description="Are you sure you want to restore all settings to default configurations? This will override current settings."
            onConfirm={() => resetSettingsMutation.mutate()}
            okText="Yes, Reset"
            cancelText="No"
            icon={<WarningOutlined style={{ color: '#fa8c16' }} />}
          >
            <Button icon={<ReloadOutlined />}>
              Restore Factory Defaults
            </Button>
          </Popconfirm>
        </Space>
      </div>

      {/* Main Settings Form */}
      <Form
        form={form}
        layout="vertical"
        onFinish={handleFinish}
        onValuesChange={() => setIsFormDirty(true)}
        loading={isSettingsLoading}
      >
        <Card bodyStyle={{ padding: '0 24px 24px' }} style={{ boxShadow: '0 1px 3px rgba(0,0,0,0.03)' }}>
          <Tabs
            activeKey={activeTab}
            onChange={(key) => setActiveTab(key)}
            items={tabItems}
            style={{ marginBottom: 24 }}
          />

          <Form.Item style={{ margin: 0, textAlign: 'right' }}>
            <Button
              type="primary"
              htmlType="submit"
              icon={<SaveOutlined />}
              loading={updateSettingsMutation.isPending}
            >
              Save Configuration Settings
            </Button>
          </Form.Item>
        </Card>
      </Form>

      {/* Navigation Warning Modal */}
      {blocker.state === 'blocked' && (
        <Modal
          title={
            <Space>
              <WarningOutlined style={{ color: '#faad14' }} />
              <span>Unsaved Changes Detected</span>
            </Space>
          }
          open={true}
          onOk={() => blocker.proceed()}
          onCancel={() => blocker.reset()}
          okText="Discard & Leave"
          cancelText="Stay & Edit"
          okButtonProps={{ danger: true }}
        >
          <Paragraph>
            You have unsaved changes in the system configuration settings form. If you leave this page, your modifications will be lost.
          </Paragraph>
          <Paragraph type="secondary">
            Are you sure you want to discard your changes and navigate away?
          </Paragraph>
        </Modal>
      )}
    </div>
  );
};

export default Settings;
