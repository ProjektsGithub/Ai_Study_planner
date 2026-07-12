import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useBlocker, Link } from 'react-router-dom';
import apiClient from '../../api/client';
import EntityHistory from '../../components/EntityHistory';
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
  Drawer,
  Popconfirm,
  Tooltip,
  Tag,
  Spin,
  message,
} from 'antd';
import {
  BankOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  EnvironmentOutlined,
  SearchOutlined,
  FileExcelOutlined,
  ReloadOutlined,
  ArrowRightOutlined,
  WarningOutlined,
  HistoryOutlined,
} from '@ant-design/icons';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';

const { Title, Paragraph, Text } = Typography;

const Universities = () => {
  const queryClient = useQueryClient();
  const { hasRole } = useAuth();
  const isSuperAdmin = hasRole('super_admin');
  const { lang } = useLanguage();

  // Search and Pagination states
  const [searchText, setSearchText] = useState(() => sessionStorage.getItem('unis_search') || '');
  const [currentPage, setCurrentPage] = useState(() => {
    const val = sessionStorage.getItem('unis_page');
    return val ? parseInt(val, 10) : 1;
  });
  const [pageSize, setPageSize] = useState(10);

  // University Modal states
  const [uniModalOpen, setUniModalOpen] = useState(false);
  const [editingUni, setEditingUni] = useState(null);
  const [uniForm] = Form.useForm();

  // Dependents Verification state
  const [depModalOpen, setDepModalOpen] = useState(false);
  const [uniToDelete, setUniToDelete] = useState(null);
  const [depCounts, setDepCounts] = useState(null);
  const [isDepLoading, setIsDepLoading] = useState(false);

  // Campus Drawer states
  const [campusDrawerOpen, setCampusDrawerOpen] = useState(false);
  const [selectedUni, setSelectedUni] = useState(null);
  const [campusModalOpen, setCampusModalOpen] = useState(false);
  const [editingCampus, setEditingCampus] = useState(null);
  const [campusForm] = Form.useForm();

  // History Drawer states
  const [historyDrawerOpen, setHistoryDrawerOpen] = useState(false);
  const [historyEntityId, setHistoryEntityId] = useState(null);

  // Dirty form states
  const [isFormDirty, setIsFormDirty] = useState(false);
  const [isCampusFormDirty, setIsCampusFormDirty] = useState(false);

  const blocker = useBlocker(
    ({ currentValue, nextLocation }) =>
      (isFormDirty || isCampusFormDirty) && currentValue.pathname !== nextLocation.pathname
  );

  const germanTextRule = {
    pattern: /^[a-zA-ZäöüßÄÖÜ0-9\s\.,\-\(\)\/\':;&\!?%@#\+\*\[\]]*$/,
    message: 'Invalid characters. German letters (ä, ö, ü, ß) and common punctuation are supported.',
  };

  // 1. Fetch universities
  const {
    data: uniData,
    isLoading: isUniLoading,
    refetch: refetchUnis,
  } = useQuery({
    queryKey: ['adminUniversities', currentPage, pageSize, searchText],
    queryFn: async () => {
      const skip = (currentPage - 1) * pageSize;
      const params = { skip, limit: pageSize };
      if (searchText) {
        params.search = searchText;
      }
      const response = await apiClient.get('/api/v1/admin/universities', { params });
      return response.data;
    },
  });

  // 2. Fetch campuses (only active when campus drawer is open)
  const {
    data: campusData,
    isLoading: isCampusLoading,
    refetch: refetchCampuses,
  } = useQuery({
    queryKey: ['adminCampuses', selectedUni?.id],
    queryFn: async () => {
      if (!selectedUni?.id) return { campuses: [], total: 0 };
      const response = await apiClient.get(`/api/v1/admin/campuses?university_id=${selectedUni.id}`);
      return response.data;
    },
    enabled: !!selectedUni?.id,
  });

  // 3. Mutations for Universities
  const createUniMutation = useMutation({
    mutationFn: async (values) => {
      const response = await apiClient.post('/api/v1/admin/universities', values);
      return response.data;
    },
    onSuccess: () => {
      message.success('University created successfully.');
      setIsFormDirty(false);
      setUniModalOpen(false);
      uniForm.resetFields();
      queryClient.invalidateQueries({ queryKey: ['adminUniversities'] });
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || 'Failed to create university.');
    },
  });

  const updateUniMutation = useMutation({
    mutationFn: async ({ id, values }) => {
      const response = await apiClient.put(`/api/v1/admin/universities/${id}`, values);
      return response.data;
    },
    onSuccess: () => {
      message.success('University updated successfully.');
      setIsFormDirty(false);
      setUniModalOpen(false);
      setEditingUni(null);
      uniForm.resetFields();
      queryClient.invalidateQueries({ queryKey: ['adminUniversities'] });
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || 'Failed to update university.');
    },
  });

  const deleteUniMutation = useMutation({
    mutationFn: async (id) => {
      const response = await apiClient.delete(`/api/v1/admin/universities/${id}`);
      return response.data;
    },
    onSuccess: () => {
      message.success('University soft-deleted successfully.');
      setDepModalOpen(false);
      setUniToDelete(null);
      setDepCounts(null);
      queryClient.invalidateQueries({ queryKey: ['adminUniversities'] });
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || 'Failed to delete university.');
    },
  });

  // 4. Mutations for Campuses
  const createCampusMutation = useMutation({
    mutationFn: async (values) => {
      const response = await apiClient.post('/api/v1/admin/campuses', values);
      return response.data;
    },
    onSuccess: () => {
      message.success('Campus created successfully.');
      setIsCampusFormDirty(false);
      setCampusModalOpen(false);
      campusForm.resetFields();
      queryClient.invalidateQueries({ queryKey: ['adminCampuses'] });
      queryClient.invalidateQueries({ queryKey: ['adminUniversities'] }); // Update campus count on main table
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || 'Failed to create campus.');
    },
  });

  const updateCampusMutation = useMutation({
    mutationFn: async ({ id, values }) => {
      const response = await apiClient.put(`/api/v1/admin/campuses/${id}`, values);
      return response.data;
    },
    onSuccess: () => {
      message.success('Campus updated successfully.');
      setIsCampusFormDirty(false);
      setCampusModalOpen(false);
      setEditingCampus(null);
      campusForm.resetFields();
      queryClient.invalidateQueries({ queryKey: ['adminCampuses'] });
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || 'Failed to update campus.');
    },
  });

  const deleteCampusMutation = useMutation({
    mutationFn: async (id) => {
      const response = await apiClient.delete(`/api/v1/admin/campuses/${id}`);
      return response.data;
    },
    onSuccess: () => {
      message.success('Campus soft-deleted successfully.');
      queryClient.invalidateQueries({ queryKey: ['adminCampuses'] });
      queryClient.invalidateQueries({ queryKey: ['adminUniversities'] });
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || 'Failed to delete campus.');
    },
  });

  // Handle University Form Submit
  const handleUniSubmit = (values) => {
    if (editingUni) {
      updateUniMutation.mutate({ id: editingUni.id, values });
    } else {
      createUniMutation.mutate(values);
    }
  };

  // Open Edit University Modal
  const showEditUniModal = (record) => {
    setEditingUni(record);
    setIsFormDirty(false);
    uniForm.setFieldsValue({
      name: record.name,
      name_de: record.name_de,
      country: record.country || 'Germany',
      description: record.description,
      description_de: record.description_de,
    });
    setUniModalOpen(true);
  };

  // Open Create University Modal
  const showCreateUniModal = () => {
    setEditingUni(null);
    setIsFormDirty(false);
    uniForm.resetFields();
    uniForm.setFieldsValue({ country: 'Germany' });
    setUniModalOpen(true);
  };

  const handleCancelUniModal = () => {
    if (isFormDirty) {
      Modal.confirm({
        title: 'Discard unsaved changes?',
        content: 'You have unsaved university profile changes. Are you sure you want to discard them?',
        okText: 'Yes, Discard',
        cancelText: 'No, Keep Editing',
        onOk: () => {
          setUniModalOpen(false);
          setIsFormDirty(false);
          uniForm.resetFields();
        },
      });
    } else {
      setUniModalOpen(false);
      uniForm.resetFields();
    }
  };

  // Handle Deletion dependents check
  const showDeleteUniWarning = async (record) => {
    setUniToDelete(record);
    setIsDepLoading(true);
    setDepModalOpen(true);
    try {
      const response = await apiClient.get(`/api/v1/admin/universities/${record.id}/dependents`);
      setDepCounts(response.data);
    } catch (err) {
      message.error('Failed to query dependent entity counts.');
      setDepModalOpen(false);
    } finally {
      setIsDepLoading(false);
    }
  };

  // Confirm delete university
  const handleConfirmDeleteUni = () => {
    if (uniToDelete) {
      deleteUniMutation.mutate(uniToDelete.id);
    }
  };

  // Excel Export blobs download handler
  const handleExportExcel = async (uniId = null) => {
    try {
      const url = uniId
        ? `/api/v1/admin/exports/curriculum/excel?university_id=${uniId}`
        : '/api/v1/admin/exports/curriculum/excel';

      const response = await apiClient.get(url, { responseType: 'blob' });
      const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      });
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;

      const dateStr = new Date().toISOString().slice(0, 10);
      const filename = uniId
        ? `curriculum_uni_${uniId}_${dateStr}.xlsx`
        : `curriculum_all_${dateStr}.xlsx`;

      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
      message.success('Curriculum Excel sheets downloaded successfully.');
    } catch (err) {
      console.error('Excel export error:', err);
      message.error('Excel workbook generation failed.');
    }
  };

  // Open Campuses sub-drawer
  const openCampusesDrawer = (record) => {
    setSelectedUni(record);
    setCampusDrawerOpen(true);
  };

  // Handle Campus Form Submit
  const handleCampusSubmit = (values) => {
    const payload = { ...values, university_id: selectedUni.id };
    if (editingCampus) {
      updateCampusMutation.mutate({ id: editingCampus.id, values: payload });
    } else {
      createCampusMutation.mutate(payload);
    }
  };

  // Open Edit Campus Modal
  const showEditCampusModal = (record) => {
    setEditingCampus(record);
    setIsCampusFormDirty(false);
    campusForm.setFieldsValue({
      name: record.name,
      name_de: record.name_de,
      location: record.location,
      description: record.description,
      description_de: record.description_de,
    });
    setCampusModalOpen(true);
  };

  // Open Create Campus Modal
  const showCreateCampusModal = () => {
    setEditingCampus(null);
    setIsCampusFormDirty(false);
    campusForm.resetFields();
    setCampusModalOpen(true);
  };

  const handleCancelCampusModal = () => {
    if (isCampusFormDirty) {
      Modal.confirm({
        title: 'Discard unsaved changes?',
        content: 'You have unsaved campus modifications. Are you sure you want to discard them?',
        okText: 'Yes, Discard',
        cancelText: 'No, Keep Editing',
        onOk: () => {
          setCampusModalOpen(false);
          setIsCampusFormDirty(false);
          campusForm.resetFields();
        },
      });
    } else {
      setCampusModalOpen(false);
      campusForm.resetFields();
    }
  };

  // Universities Columns definition
  const columns = [
    {
      title: lang === 'de' ? 'Name der Universität' : 'University Name',
      key: 'name',
      render: (_, record) => {
        const primary = lang === 'de' ? (record.name_de || record.name) : (record.name || record.name_de);
        const secondary = lang === 'de' ? (record.name_de ? record.name : '') : (record.name ? record.name_de : '');
        return (
          <Space direction="vertical" size={0}>
            <Text strong style={{ fontSize: 14 }}>{primary}</Text>
            {secondary && (
              <Text type="secondary" style={{ fontSize: 12 }}>
                {lang === 'de' ? `EN: ${secondary}` : `DE: ${secondary}`}
              </Text>
            )}
          </Space>
        );
      },
    },
    {
      title: lang === 'de' ? 'Land' : 'Country',
      dataIndex: 'country',
      key: 'country',
      width: 140,
      render: (text) => <Tag color="blue">{text || 'Germany'}</Tag>,
    },
    {
      title: lang === 'de' ? 'Beschreibung' : 'Description',
      key: 'description',
      ellipsis: true,
      render: (_, record) => {
        return lang === 'de' ? (record.description_de || record.description || '—') : (record.description || record.description_de || '—');
      },
    },
    {
      title: 'Campuses',
      key: 'campuses',
      width: 130,
      render: (_, record) => (
        <Button
          type="link"
          icon={<EnvironmentOutlined />}
          onClick={() => openCampusesDrawer(record)}
        >
          {record.campus_count ?? 0} Campuses
        </Button>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 220,
      render: (_, record) => (
        <Space size={8}>
          <Tooltip title="Edit Profile">
            <Button
              type="text"
              icon={<EditOutlined style={{ color: '#1890ff' }} />}
              onClick={() => showEditUniModal(record)}
            />
          </Tooltip>
          {isSuperAdmin && (
            <Tooltip title="View Change History">
              <Button
                type="text"
                icon={<HistoryOutlined style={{ color: '#fa8c16' }} />}
                onClick={() => {
                  setHistoryEntityId(record.id);
                  setHistoryDrawerOpen(true);
                }}
              />
            </Tooltip>
          )}
          {isSuperAdmin ? (
            <Tooltip title="Delete University">
              <Button
                type="text"
                icon={<DeleteOutlined style={{ color: '#f5222d' }} />}
                onClick={() => showDeleteUniWarning(record)}
              />
            </Tooltip>
          ) : null}
          <Tooltip title="Export Excel Report">
            <Button
              type="text"
              icon={<FileExcelOutlined style={{ color: '#52c41a' }} />}
              onClick={() => handleExportExcel(record.id)}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  // Campuses Columns definition inside drawer
  const campusColumns = [
    {
      title: 'Campus Name',
      key: 'name',
      render: (_, record) => (
        <Space direction="vertical" size={0}>
          <Text strong style={{ fontSize: 13 }}>{record.name}</Text>
          {record.name_de && (
            <Text type="secondary" style={{ fontSize: 11 }}>
              DE: {record.name_de}
            </Text>
          )}
        </Space>
      ),
    },
    {
      title: 'Location',
      dataIndex: 'location',
      key: 'location',
      render: (text) => <Text style={{ fontSize: 13 }}>{text}</Text>,
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 120,
      render: (_, record) => (
        <Space size={8}>
          <Button
            type="text"
            icon={<EditOutlined style={{ color: '#1890ff' }} />}
            onClick={() => showEditCampusModal(record)}
          />
          <Popconfirm
            title="Delete Campus?"
            description="Are you sure you want to delete this campus?"
            okText="Yes"
            cancelText="No"
            onConfirm={() => deleteCampusMutation.mutate(record.id)}
          >
            <Button type="text" icon={<DeleteOutlined style={{ color: '#f5222d' }} />} />
          </Popconfirm>
        </Space>
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
            <Breadcrumb.Item>Universities</Breadcrumb.Item>
          </Breadcrumb>
          <Title level={2} style={{ margin: 0 }}>University Profiles</Title>
          <Paragraph style={{ margin: 0, marginTop: 4 }}>
            Manage the list of universities, their respective campuses, and export curriculum schemas.
          </Paragraph>
        </div>

        <Space>
          <Button
            type="default"
            icon={<FileExcelOutlined />}
            onClick={() => handleExportExcel()}
            style={{ color: '#52c41a', borderColor: '#52c41a' }}
          >
            Export All to Excel
          </Button>
          {isSuperAdmin && (
            <Button type="primary" icon={<PlusOutlined />} onClick={showCreateUniModal}>
              Add University
            </Button>
          )}
        </Space>
      </div>

      {/* Filter and Search Panel */}
      <Card style={{ marginBottom: 24, boxShadow: '0 1px 2px rgba(0,0,0,0.03)' }} bodyStyle={{ padding: '16px 24px' }}>
        <Row gutter={16}>
          <Col xs={24} md={12} lg={8}>
            <Input
              placeholder="Search universities by name or description..."
              prefix={<SearchOutlined style={{ color: '#bfbfbf' }} />}
              value={searchText}
              onChange={(e) => {
                const val = e.target.value;
                setSearchText(val);
                sessionStorage.setItem('unis_search', val);
                setCurrentPage(1);
                sessionStorage.setItem('unis_page', '1');
              }}
              allowClear
            />
          </Col>
          <Col xs={24} md={12} lg={16} style={{ textAlign: 'right' }}>
            <Button icon={<ReloadOutlined />} onClick={() => refetchUnis()}>
              Reload
            </Button>
          </Col>
        </Row>
      </Card>

      {/* Main Table */}
      <Table
        scroll={{ x: 'max-content' }}
        columns={columns}
        dataSource={uniData?.universities || []}
        rowKey="id"
        loading={isUniLoading}
        pagination={{
          current: currentPage,
          pageSize: pageSize,
          total: uniData?.total || 0,
          showSizeChanger: true,
          pageSizeOptions: ['5', '10', '20', '50'],
          onChange: (p, ps) => {
            setCurrentPage(p);
            sessionStorage.setItem('unis_page', String(p));
            setPageSize(ps);
          },
        }}
        locale={{
          emptyText: 'No universities found matching criteria.',
        }}
      />

      {/* University Add/Edit Modal */}
      <Modal
        title={editingUni ? 'Edit University Profile' : 'Register New University'}
        open={uniModalOpen}
        onCancel={handleCancelUniModal}
        footer={null}
        destroyOnClose
      >
        <Form
          form={uniForm}
          layout="vertical"
          onFinish={handleUniSubmit}
          onValuesChange={() => setIsFormDirty(true)}
          style={{ marginTop: 16 }}
        >
          <Form.Item
            name="name"
            label="University Name (English)"
            rules={[
              { required: true, message: 'Please input the university name in English' },
              { max: 255, message: 'Must be 255 characters or less' },
              germanTextRule,
            ]}
          >
            <Input placeholder="e.g. Technical University of Munich" />
          </Form.Item>

          <Form.Item
            name="name_de"
            label="University Name (German)"
            rules={[
              { max: 255, message: 'Must be 255 characters or less' },
              germanTextRule,
            ]}
          >
            <Input placeholder="e.g. Technische Universität München" />
          </Form.Item>

          <Form.Item
            name="country"
            label="Country"
            rules={[
              { required: true, message: 'Please specify the country' },
              germanTextRule,
            ]}
          >
            <Input placeholder="e.g. Germany" />
          </Form.Item>

          <Form.Item
            name="description"
            label="English Description"
            rules={[germanTextRule]}
          >
            <Input.TextArea rows={3} placeholder="Provide a brief summary of the institution in English..." />
          </Form.Item>

          <Form.Item
            name="description_de"
            label="German Description"
            rules={[germanTextRule]}
          >
            <Input.TextArea rows={3} placeholder="Beschreibung auf Deutsch..." />
          </Form.Item>

          <Form.Item style={{ textAlign: 'right', marginBottom: 0, marginTop: 24 }}>
            <Space>
              <Button onClick={handleCancelUniModal}>Cancel</Button>
              <Button
                type="primary"
                htmlType="submit"
                loading={createUniMutation.isPending || updateUniMutation.isPending}
              >
                {editingUni ? 'Save Changes' : 'Create Profile'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* Dependents Deletion Warning Modal */}
      <Modal
        title={
          <Space>
            <WarningOutlined style={{ color: '#f5222d' }} />
            <span>Confirm Deletion Impact</span>
          </Space>
        }
        open={depModalOpen}
        onCancel={() => setDepModalOpen(false)}
        onOk={handleConfirmDeleteUni}
        okText="Yes, Soft-Delete University"
        okButtonProps={{
          danger: true,
          loading: deleteUniMutation.isPending,
        }}
        confirmLoading={deleteUniMutation.isPending}
        destroyOnClose
      >
        <div style={{ marginTop: 16 }}>
          <Paragraph>
            Are you sure you want to delete university <Text strong>{uniToDelete?.name}</Text>?
          </Paragraph>
          <Paragraph type="secondary">
            This action performs a soft deletion. It will mark the university and its associated campuses as deleted.
          </Paragraph>

          <Spin spinning={isDepLoading}>
            {depCounts && (
              <Card
                size="small"
                title="Dependent Entities Affected:"
                style={{ background: '#fff1f0', borderColor: '#ffa39e', marginTop: 16 }}
              >
                <ul style={{ paddingLeft: 20, margin: 0 }}>
                  <li>Campuses to delete: <Text strong>{depCounts.campuses ?? 0}</Text></li>
                  <li>Linked Study Programs affected: <Text strong>{depCounts.programs ?? 0}</Text></li>
                  <li>Academic Tracks: <Text strong>{depCounts.tracks ?? 0}</Text></li>
                  <li>Semesters: <Text strong>{depCounts.semesters ?? 0}</Text></li>
                  <li>Courses: <Text strong>{depCounts.courses ?? 0}</Text></li>
                </ul>
              </Card>
            )}
          </Spin>
        </div>
      </Modal>

      {/* Campuses Sub-drawer */}
      <Drawer
        title={`Campuses: ${selectedUni?.name}`}
        placement="right"
        width={650}
        onClose={() => setCampusDrawerOpen(false)}
        open={campusDrawerOpen}
        destroyOnClose
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <Text type="secondary">List and configure physical campus branches.</Text>
          <Button type="primary" size="small" icon={<PlusOutlined />} onClick={showCreateCampusModal}>
            New Campus
          </Button>
        </div>

        <Table
          columns={campusColumns}
          dataSource={campusData?.campuses || []}
          rowKey="id"
          loading={isCampusLoading}
          pagination={false}
          locale={{
            emptyText: 'No campus records registered for this university.',
          }}
        />
      </Drawer>

      {/* Campus Form Modal */}
      <Modal
        title={editingCampus ? 'Edit Campus Details' : 'Add New Campus Branch'}
        open={campusModalOpen}
        onCancel={handleCancelCampusModal}
        footer={null}
        destroyOnClose
      >
        <Form
          form={campusForm}
          layout="vertical"
          onFinish={handleCampusSubmit}
          onValuesChange={() => setIsCampusFormDirty(true)}
          style={{ marginTop: 16 }}
        >
          <Form.Item
            name="name"
            label="Campus Name (English)"
            rules={[
              { required: true, message: 'Please input the campus name' },
              { max: 255, message: 'Must be 255 characters or less' },
              germanTextRule,
            ]}
          >
            <Input placeholder="e.g. Garching Campus" />
          </Form.Item>

          <Form.Item
            name="name_de"
            label="Campus Name (German)"
            rules={[
              { max: 255, message: 'Must be 255 characters or less' },
              germanTextRule,
            ]}
          >
            <Input placeholder="e.g. Campus Garching" />
          </Form.Item>

          <Form.Item
            name="location"
            label="Location / Address"
            rules={[
              { required: true, message: 'Please input the physical location' },
              germanTextRule,
            ]}
          >
            <Input placeholder="e.g. Boltzmannstraße 15, 85748 Garching bei München" />
          </Form.Item>

          <Form.Item
            name="description"
            label="English Description"
            rules={[germanTextRule]}
          >
            <Input.TextArea rows={3} placeholder="Details about this campus branch..." />
          </Form.Item>

          <Form.Item
            name="description_de"
            label="German Description"
            rules={[germanTextRule]}
          >
            <Input.TextArea rows={3} placeholder="Beschreibung des Standorts..." />
          </Form.Item>

          <Form.Item style={{ textAlign: 'right', marginBottom: 0, marginTop: 24 }}>
            <Space>
              <Button onClick={handleCancelCampusModal}>Cancel</Button>
              <Button
                type="primary"
                htmlType="submit"
                loading={createCampusMutation.isPending || updateCampusMutation.isPending}
              >
                {editingCampus ? 'Save Changes' : 'Add Campus'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* History Drawer */}
      <Drawer
        title="University Change History"
        placement="right"
        width={480}
        onClose={() => {
          setHistoryDrawerOpen(false);
          setHistoryEntityId(null);
        }}
        open={historyDrawerOpen}
        destroyOnClose
      >
        <EntityHistory entityType="university" entityId={historyEntityId} />
      </Drawer>

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

export default Universities;
