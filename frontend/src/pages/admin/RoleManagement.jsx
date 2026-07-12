import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate, useBlocker, Link } from 'react-router-dom';
import apiClient from '../../api/client';
import {
  Table,
  Button,
  Input,
  Space,
  Card,
  Typography,
  Breadcrumb,
  Modal,
  Form,
  Row,
  Col,
  Select,
  Tag,
  Tooltip,
  Popconfirm,
  Result,
  InputNumber,
  message,
} from 'antd';
import {
  UsergroupAddOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SearchOutlined,
  ReloadOutlined,
  SafetyCertificateOutlined,
  WarningOutlined,
} from '@ant-design/icons';
import { useAuth } from '../../context/AuthContext';

const { Title, Paragraph, Text } = Typography;
const { Option } = Select;

const RoleManagement = () => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { hasRole, user: currentUser } = useAuth();
  const isSuperAdmin = hasRole('super_admin');

  // Table filtering and search states
  const [filterUserId, setFilterUserId] = useState(() => {
    const val = sessionStorage.getItem('roles_user_id');
    return val ? parseInt(val, 10) : undefined;
  });
  const [filterRoleName, setFilterRoleName] = useState(() => sessionStorage.getItem('roles_role_name') || undefined);
  const [currentPage, setCurrentPage] = useState(() => {
    const val = sessionStorage.getItem('roles_page');
    return val ? parseInt(val, 10) : 1;
  });
  const [pageSize, setPageSize] = useState(10);

  // Assignment Modal states
  const [modalOpen, setModalOpen] = useState(false);
  const [editingAssignment, setEditingAssignment] = useState(null);
  const [form] = Form.useForm();
  const watchRoleName = Form.useWatch('role_name', form);

  // Dirty form state
  const [isFormDirty, setIsFormDirty] = useState(false);

  const blocker = useBlocker(
    ({ currentValue, nextLocation }) =>
      isFormDirty && currentValue.pathname !== nextLocation.pathname
  );

  // 1. Fetch available role definitions
  const { data: roleDefsData } = useQuery({
    queryKey: ['adminRoleDefinitions'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/admin/roles/definitions');
      return response.data;
    },
    enabled: isSuperAdmin,
  });

  // 2. Fetch all universities for scopes
  const { data: universitiesData } = useQuery({
    queryKey: ['allUniversitiesList'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/admin/universities?limit=200');
      return response.data;
    },
    enabled: isSuperAdmin,
  });

  // 3. Fetch all study programs for scopes
  const { data: programsData } = useQuery({
    queryKey: ['allProgramsList'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/admin/programs?limit=200');
      return response.data;
    },
    enabled: isSuperAdmin,
  });

  // 4. Fetch role assignments (paginated)
  const {
    data: assignmentsData,
    isLoading: isAssignmentsLoading,
    refetch: refetchAssignments,
  } = useQuery({
    queryKey: ['adminRoleAssignments', currentPage, pageSize, filterUserId, filterRoleName],
    queryFn: async () => {
      const skip = (currentPage - 1) * pageSize;
      const params = { skip, limit: pageSize };
      if (filterUserId) params.user_id = filterUserId;
      if (filterRoleName) params.role_name = filterRoleName;

      const response = await apiClient.get('/api/v1/admin/roles', { params });
      return response.data;
    },
    enabled: isSuperAdmin,
  });

  // 5. CRUD Mutations
  const assignRoleMutation = useMutation({
    mutationFn: async (values) => {
      const response = await apiClient.post('/api/v1/admin/roles/assign', values);
      return response.data;
    },
    onSuccess: () => {
      message.success('Role assigned successfully.');
      setIsFormDirty(false);
      setModalOpen(false);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['adminRoleAssignments'] });
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || 'Failed to assign role.');
    },
  });

  const updateRoleMutation = useMutation({
    mutationFn: async ({ id, values }) => {
      const response = await apiClient.put(`/api/v1/admin/roles/${id}`, values);
      return response.data;
    },
    onSuccess: () => {
      message.success('Role assignment updated successfully.');
      setIsFormDirty(false);
      setModalOpen(false);
      setEditingAssignment(null);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['adminRoleAssignments'] });
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || 'Failed to update role assignment.');
    },
  });

  const revokeRoleMutation = useMutation({
    mutationFn: async (id) => {
      const response = await apiClient.delete(`/api/v1/admin/roles/${id}`);
      return response.data;
    },
    onSuccess: (data) => {
      message.success(data.message || 'Role assignment revoked successfully.');
      queryClient.invalidateQueries({ queryKey: ['adminRoleAssignments'] });
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || 'Failed to revoke role assignment.');
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
            subTitle="Sorry, only Super Administrators are authorized to manage user roles and scopes."
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

  const handleFormSubmit = (values) => {
    const payload = {
      user_id: values.user_id,
      role_name: values.role_name,
      university_id: values.role_name === 'university_admin' ? values.university_id : null,
      program_id: values.role_name === 'program_coordinator' ? values.program_id : null,
    };

    if (editingAssignment) {
      updateRoleMutation.mutate({ id: editingAssignment.id, values: payload });
    } else {
      assignRoleMutation.mutate(payload);
    }
  };

  const showCreateModal = () => {
    setEditingAssignment(null);
    setIsFormDirty(false);
    form.resetFields();
    setModalOpen(true);
  };

  const showEditModal = (record) => {
    setEditingAssignment(record);
    setIsFormDirty(false);
    form.setFieldsValue({
      user_id: record.user_id,
      role_name: record.role_name,
      university_id: record.university_id || undefined,
      program_id: record.program_id || undefined,
    });
    setModalOpen(true);
  };

  const handleCancelRoleModal = () => {
    if (isFormDirty) {
      Modal.confirm({
        title: 'Discard unsaved changes?',
        content: 'You have unsaved role assignment changes. Are you sure you want to discard them?',
        okText: 'Yes, Discard',
        cancelText: 'No, Keep Editing',
        onOk: () => {
          setModalOpen(false);
          setIsFormDirty(false);
          form.resetFields();
        },
      });
    } else {
      setModalOpen(false);
      form.resetFields();
    }
  };

  const universityMap = {};
  universitiesData?.universities?.forEach((u) => {
    universityMap[u.id] = u.name;
  });

  const programMap = {};
  programsData?.programs?.forEach((p) => {
    programMap[p.id] = `${p.name} (${p.code})`;
  });

  const roleTags = {
    super_admin: <Tag color="gold" style={{ fontWeight: 'bold' }}>SUPER ADMIN</Tag>,
    university_admin: <Tag color="blue" style={{ fontWeight: 'bold' }}>UNIVERSITY ADMIN</Tag>,
    program_coordinator: <Tag color="purple" style={{ fontWeight: 'bold' }}>COORDINATOR</Tag>,
  };

  const columns = [
    {
      title: 'Assignment ID',
      dataIndex: 'id',
      key: 'id',
      width: 130,
      render: (id) => <Text strong>#{id}</Text>,
    },
    {
      title: 'User Profile',
      key: 'user',
      render: (_, record) => (
        <Space direction="vertical" size={0}>
          <Text strong style={{ fontSize: '13.5px' }}>{record.user_name || '—'}</Text>
          <Text type="secondary" style={{ fontSize: '11px' }}>
            Email: {record.user_email || '—'} (ID: {record.user_id})
          </Text>
        </Space>
      ),
    },
    {
      title: 'Assigned Role',
      dataIndex: 'role_name',
      key: 'role_name',
      width: 180,
      render: (name) => roleTags[name] || <Tag>{name?.toUpperCase()}</Tag>,
    },
    {
      title: 'Scoped Limits / Access',
      key: 'scope',
      render: (_, record) => {
        if (record.role_name === 'super_admin') {
          return <Tag color="cyan">Global (No boundaries)</Tag>;
        }
        if (record.role_name === 'university_admin') {
          const name = universityMap[record.university_id] || `University #${record.university_id}`;
          return (
            <Space direction="vertical" size={0}>
              <Text style={{ fontSize: '13px' }}>{name}</Text>
              <Text type="secondary" style={{ fontSize: '10.5px' }}>Scope: University ID {record.university_id}</Text>
            </Space>
          );
        }
        if (record.role_name === 'program_coordinator') {
          const name = programMap[record.program_id] || `Study Program #${record.program_id}`;
          return (
            <Space direction="vertical" size={0}>
              <Text style={{ fontSize: '13px' }}>{name}</Text>
              <Text type="secondary" style={{ fontSize: '10.5px' }}>Scope: Program ID {record.program_id}</Text>
            </Space>
          );
        }
        return '—';
      },
    },
    {
      title: 'Assigned Date',
      dataIndex: 'assigned_at',
      key: 'assigned_at',
      width: 160,
      render: (date) => {
        if (!date) return <Text>—</Text>;
        const d = new Date(date);
        const day = String(d.getDate()).padStart(2, '0');
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const year = d.getFullYear();
        return <Text style={{ fontSize: '12px' }}>{`${day}.${month}.${year}`}</Text>;
      },
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 140,
      render: (_, record) => {
        const isSelf = record.user_id === currentUser?.id;
        const isSelfSuperAdmin = isSelf && record.role_name === 'super_admin';

        return (
          <Space size={8}>
            <Tooltip title={isSelfSuperAdmin ? 'Cannot edit your own primary role' : 'Edit Scope'}>
              <Button
                type="text"
                icon={<EditOutlined style={{ color: isSelfSuperAdmin ? '#bfbfbf' : '#1890ff' }} />}
                onClick={() => showEditModal(record)}
                disabled={isSelfSuperAdmin}
              />
            </Tooltip>
            <Tooltip title={isSelfSuperAdmin ? 'Cannot revoke your own primary role' : 'Revoke Role'}>
              <Popconfirm
                title="Revoke Role?"
                description={`Are you sure you want to revoke the role from this user?`}
                okText="Yes"
                cancelText="No"
                onConfirm={() => revokeRoleMutation.mutate(record.id)}
                disabled={isSelfSuperAdmin}
                icon={<WarningOutlined style={{ color: '#f5222d' }} />}
              >
                <Button
                  type="text"
                  icon={<DeleteOutlined style={{ color: isSelfSuperAdmin ? '#bfbfbf' : '#f5222d' }} />}
                  disabled={isSelfSuperAdmin}
                />
              </Popconfirm>
            </Tooltip>
          </Space>
        );
      },
    },
  ];

  return (
    <div style={{ padding: '24px', background: '#fff', borderRadius: 8, minHeight: '100%' }}>
      {/* Header section */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16, marginBottom: 24 }}>
        <div>
          <Breadcrumb style={{ marginBottom: 8 }}>
            <Breadcrumb.Item><Link to="/admin/dashboard">Admin Platform</Link></Breadcrumb.Item>
            <Breadcrumb.Item>User Roles</Breadcrumb.Item>
          </Breadcrumb>
          <Title level={2} style={{ margin: 0 }}>Role & Scope Assignments</Title>
          <Paragraph style={{ margin: 0, marginTop: 4 }}>
            Assign administrative access levels (Super Admin, University Admin, Program Coordinator) and restrict them to specific scopes.
          </Paragraph>
        </div>

        <Button type="primary" icon={<PlusOutlined />} onClick={showCreateModal}>
          Assign New Role
        </Button>
      </div>

      {/* Filter panel */}
      <Card style={{ marginBottom: 24, boxShadow: '0 1px 2px rgba(0,0,0,0.03)' }} bodyStyle={{ padding: '16px 24px' }}>
        <Row gutter={16} align="middle">
          <Col xs={24} md={8}>
            <InputNumber
              placeholder="Search by User ID..."
              style={{ width: '100%' }}
              value={filterUserId}
              onChange={(val) => {
                setFilterUserId(val || undefined);
                if (val) {
                  sessionStorage.setItem('roles_user_id', String(val));
                } else {
                  sessionStorage.removeItem('roles_user_id');
                }
                setCurrentPage(1);
                sessionStorage.setItem('roles_page', '1');
              }}
              min={1}
            />
          </Col>
          <Col xs={24} md={8}>
            <Select
              style={{ width: '100%' }}
              placeholder="Filter by Role"
              value={filterRoleName}
              onChange={(val) => {
                setFilterRoleName(val || undefined);
                if (val) {
                  sessionStorage.setItem('roles_role_name', val);
                } else {
                  sessionStorage.removeItem('roles_role_name');
                }
                setCurrentPage(1);
                sessionStorage.setItem('roles_page', '1');
              }}
              allowClear
            >
              {roleDefsData?.roles?.map((def) => (
                <Option key={def.name} value={def.name}>
                  {def.display_name}
                </Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} md={8} style={{ textAlign: 'right' }}>
            <Button
              icon={<ReloadOutlined />}
              onClick={() => {
                setFilterUserId(undefined);
                setFilterRoleName(undefined);
                setCurrentPage(1);
                sessionStorage.removeItem('roles_user_id');
                sessionStorage.removeItem('roles_role_name');
                sessionStorage.setItem('roles_page', '1');
                refetchAssignments();
              }}
            >
              Reset Filters
            </Button>
          </Col>
        </Row>
      </Card>

      {/* Main Table */}
      <Table
        scroll={{ x: 'max-content' }}
        columns={columns}
        dataSource={assignmentsData?.assignments || []}
        rowKey="id"
        loading={isAssignmentsLoading}
        pagination={{
          current: currentPage,
          pageSize: pageSize,
          total: assignmentsData?.total || 0,
          showSizeChanger: true,
          pageSizeOptions: ['5', '10', '20', '50'],
          onChange: (p, ps) => {
            setCurrentPage(p);
            sessionStorage.setItem('roles_page', String(p));
            setPageSize(ps);
          },
        }}
        locale={{
          emptyText: 'No user role assignments found.',
        }}
      />

      {/* Add / Edit Assignment Modal */}
      <Modal
        title={editingAssignment ? 'Edit Role Scope' : 'Assign New Administrative Role'}
        open={modalOpen}
        onCancel={handleCancelRoleModal}
        footer={null}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleFormSubmit}
          onValuesChange={() => setIsFormDirty(true)}
          style={{ marginTop: 16 }}
        >
          <Form.Item
            name="user_id"
            label="User ID (Numeric)"
            rules={[
              { required: true, message: 'Please specify the numeric User ID' },
              {
                validator: (_, value) => {
                  if (value && (isNaN(value) || parseInt(value) <= 0)) {
                    return Promise.reject(new Error('User ID must be a positive integer'));
                  }
                  return Promise.resolve();
                },
              },
            ]}
          >
            <InputNumber
              style={{ width: '100%' }}
              placeholder="e.g. 52"
              disabled={!!editingAssignment}
              min={1}
            />
          </Form.Item>

          <Form.Item
            name="role_name"
            label="Administrative Role"
            rules={[{ required: true, message: 'Please select a role' }]}
          >
            <Select placeholder="Choose access tier...">
              {roleDefsData?.roles?.map((def) => (
                <Option key={def.name} value={def.name}>
                  {def.display_name}
                </Option>
              ))}
            </Select>
          </Form.Item>

          {watchRoleName === 'university_admin' && (
            <Form.Item
              name="university_id"
              label="Scoped University boundary"
              rules={[{ required: true, message: 'Please select a university to scope the admin role' }]}
            >
              <Select placeholder="Limit admin access to university...">
                {universitiesData?.universities?.map((uni) => (
                  <Option key={uni.id} value={uni.id}>
                    {uni.name} ({uni.country})
                  </Option>
                ))}
              </Select>
            </Form.Item>
          )}

          {watchRoleName === 'program_coordinator' && (
            <Form.Item
              name="program_id"
              label="Scoped Study Program boundary"
              rules={[{ required: true, message: 'Please select a study program to scope the role' }]}
            >
              <Select placeholder="Limit coordinator access to program...">
                {programsData?.programs?.map((prog) => (
                  <Option key={prog.id} value={prog.id}>
                    {prog.name} ({prog.code})
                  </Option>
                ))}
              </Select>
            </Form.Item>
          )}

          <Form.Item style={{ textAlign: 'right', marginBottom: 0, marginTop: 24 }}>
            <Space>
              <Button onClick={handleCancelRoleModal}>Cancel</Button>
              <Button
                type="primary"
                htmlType="submit"
                loading={assignRoleMutation.isPending || updateRoleMutation.isPending}
              >
                {editingAssignment ? 'Save Assignment' : 'Assign Access'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

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
            You have unsaved changes in one of the form editors. If you leave this page, your modifications will be lost.
          </Paragraph>
          <Paragraph type="secondary">
            Are you sure you want to discard your changes and navigate away?
          </Paragraph>
        </Modal>
      )}
    </div>
  );
};

export default RoleManagement;
