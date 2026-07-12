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
  Checkbox,
  Select,
  Tag,
  Spin,
  message,
} from 'antd';
import {
  BookOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  BranchesOutlined,
  SearchOutlined,
  ReloadOutlined,
  LinkOutlined,
  WarningOutlined,
  HistoryOutlined,
} from '@ant-design/icons';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';

const { Title, Paragraph, Text } = Typography;
const { Option } = Select;

const StudyPrograms = () => {
  const queryClient = useQueryClient();
  const { hasRole } = useAuth();
  const isSuperAdmin = hasRole('super_admin');
  const { lang } = useLanguage();

  // Search and Pagination states
  const [searchText, setSearchText] = useState(() => sessionStorage.getItem('programs_search') || '');
  const [currentPage, setCurrentPage] = useState(() => {
    const val = sessionStorage.getItem('programs_page');
    return val ? parseInt(val, 10) : 1;
  });
  const [pageSize, setPageSize] = useState(10);

  // Program Modal states
  const [progModalOpen, setProgModalOpen] = useState(false);
  const [editingProg, setEditingProg] = useState(null);
  const [progForm] = Form.useForm();

  // Dependents Verification state (Program)
  const [depModalOpen, setDepModalOpen] = useState(false);
  const [progToDelete, setProgToDelete] = useState(null);
  const [depCounts, setDepCounts] = useState(null);
  const [isDepLoading, setIsDepLoading] = useState(false);

  // Link Universities states
  const [linkModalOpen, setLinkModalOpen] = useState(false);
  const [selectedProg, setSelectedProg] = useState(null);
  const [linkingUniIds, setLinkingUniIds] = useState(new Set());

  // Tracks Drawer states
  const [tracksDrawerOpen, setTracksDrawerOpen] = useState(false);
  const [tracksModalOpen, setTracksModalOpen] = useState(false);
  const [editingTrack, setEditingTrack] = useState(null);
  const [trackForm] = Form.useForm();

  // History Drawer states
  const [historyDrawerOpen, setHistoryDrawerOpen] = useState(false);
  const [historyEntityId, setHistoryEntityId] = useState(null);

  // Dirty form states
  const [isFormDirty, setIsFormDirty] = useState(false);
  const [isTrackFormDirty, setIsTrackFormDirty] = useState(false);

  const blocker = useBlocker(
    ({ currentValue, nextLocation }) =>
      (isFormDirty || isTrackFormDirty) && currentValue.pathname !== nextLocation.pathname
  );

  const germanTextRule = {
    pattern: /^[a-zA-ZäöüßÄÖÜ0-9\s\.,\-\(\)\/\':;&\!?%@#\+\*\[\]]*$/,
    message: 'Invalid characters. German letters (ä, ö, ü, ß) and common punctuation are supported.',
  };

  // Fetch all universities (for linking checkboxes)
  const { data: allUnisData } = useQuery({
    queryKey: ['allUniversitiesList'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/admin/universities?limit=200');
      return response.data;
    },
    enabled: linkModalOpen,
  });

  // Fetch linked universities for selected program
  const { data: linkedUnisData, isLoading: isLinkedUnisLoading } = useQuery({
    queryKey: ['linkedUniversities', selectedProg?.id],
    queryFn: async () => {
      if (!selectedProg?.id) return { universities: [], total: 0 };
      const response = await apiClient.get(`/api/v1/admin/programs/${selectedProg.id}/universities`);
      
      // Update local checked Set
      const ids = new Set(response.data.universities.map((u) => u.id));
      setLinkingUniIds(ids);
      return response.data;
    },
    enabled: !!selectedProg?.id && linkModalOpen,
  });

  // 1. Fetch study programs
  const {
    data: progData,
    isLoading: isProgLoading,
    refetch: refetchProgs,
  } = useQuery({
    queryKey: ['adminPrograms', currentPage, pageSize, searchText],
    queryFn: async () => {
      const skip = (currentPage - 1) * pageSize;
      const params = { skip, limit: pageSize };
      if (searchText) {
        params.search = searchText;
      }
      const response = await apiClient.get('/api/v1/admin/programs', { params });
      return response.data;
    },
  });

  // 2. Fetch academic tracks for program
  const {
    data: tracksData,
    isLoading: isTracksLoading,
    refetch: refetchTracks,
  } = useQuery({
    queryKey: ['adminTracks', selectedProg?.id],
    queryFn: async () => {
      if (!selectedProg?.id) return { tracks: [], total: 0 };
      const response = await apiClient.get(`/api/v1/admin/tracks?study_program_id=${selectedProg.id}`);
      return response.data;
    },
    enabled: !!selectedProg?.id && tracksDrawerOpen,
  });

  // 3. Mutations for Study Programs
  const createProgMutation = useMutation({
    mutationFn: async (values) => {
      const response = await apiClient.post('/api/v1/admin/programs', values);
      return response.data;
    },
    onSuccess: () => {
      message.success('Study program created successfully.');
      setIsFormDirty(false);
      setProgModalOpen(false);
      progForm.resetFields();
      queryClient.invalidateQueries({ queryKey: ['adminPrograms'] });
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || 'Failed to create program.');
    },
  });

  const updateProgMutation = useMutation({
    mutationFn: async ({ id, values }) => {
      const response = await apiClient.put(`/api/v1/admin/programs/${id}`, values);
      return response.data;
    },
    onSuccess: () => {
      message.success('Study program updated successfully.');
      setIsFormDirty(false);
      setProgModalOpen(false);
      setEditingProg(null);
      progForm.resetFields();
      queryClient.invalidateQueries({ queryKey: ['adminPrograms'] });
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || 'Failed to update program.');
    },
  });

  const deleteProgMutation = useMutation({
    mutationFn: async (id) => {
      const response = await apiClient.delete(`/api/v1/admin/programs/${id}`);
      return response.data;
    },
    onSuccess: () => {
      message.success('Study program soft-deleted successfully.');
      setDepModalOpen(false);
      setProgToDelete(null);
      setDepCounts(null);
      queryClient.invalidateQueries({ queryKey: ['adminPrograms'] });
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || 'Failed to delete program.');
    },
  });

  // 4. Mutations for Academic Tracks
  const createTrackMutation = useMutation({
    mutationFn: async (values) => {
      const response = await apiClient.post('/api/v1/admin/tracks', values);
      return response.data;
    },
    onSuccess: () => {
      message.success('Academic track created successfully.');
      setIsTrackFormDirty(false);
      setTracksModalOpen(false);
      trackForm.resetFields();
      queryClient.invalidateQueries({ queryKey: ['adminTracks'] });
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || 'Failed to create academic track.');
    },
  });

  const updateTrackMutation = useMutation({
    mutationFn: async ({ id, values }) => {
      const response = await apiClient.put(`/api/v1/admin/tracks/${id}`, values);
      return response.data;
    },
    onSuccess: () => {
      message.success('Academic track updated successfully.');
      setIsTrackFormDirty(false);
      setTracksModalOpen(false);
      setEditingTrack(null);
      trackForm.resetFields();
      queryClient.invalidateQueries({ queryKey: ['adminTracks'] });
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || 'Failed to update academic track.');
    },
  });

  const deleteTrackMutation = useMutation({
    mutationFn: async (id) => {
      const response = await apiClient.delete(`/api/v1/admin/tracks/${id}`);
      return response.data;
    },
    onSuccess: () => {
      message.success('Academic track soft-deleted successfully.');
      queryClient.invalidateQueries({ queryKey: ['adminTracks'] });
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || 'Failed to delete academic track.');
    },
  });

  // Handle Program Form Submit
  const handleProgSubmit = (values) => {
    if (editingProg) {
      updateProgMutation.mutate({ id: editingProg.id, values });
    } else {
      createProgMutation.mutate(values);
    }
  };

  // Open Edit Program Modal
  const showEditProgModal = (record) => {
    setEditingProg(record);
    setIsFormDirty(false);
    progForm.setFieldsValue({
      name: record.name,
      name_de: record.name_de,
      code: record.code,
      description: record.description,
      description_de: record.description_de,
    });
    setProgModalOpen(true);
  };

  // Open Create Program Modal
  const showCreateProgModal = () => {
    setEditingProg(null);
    setIsFormDirty(false);
    progForm.resetFields();
    setProgModalOpen(true);
  };

  const handleCancelProgModal = () => {
    if (isFormDirty) {
      Modal.confirm({
        title: 'Discard unsaved changes?',
        content: 'You have unsaved study program changes. Are you sure you want to discard them?',
        okText: 'Yes, Discard',
        cancelText: 'No, Keep Editing',
        onOk: () => {
          setProgModalOpen(false);
          setIsFormDirty(false);
          progForm.resetFields();
        },
      });
    } else {
      setProgModalOpen(false);
      progForm.resetFields();
    }
  };

  // Handle Deletion dependents check
  const showDeleteProgWarning = async (record) => {
    setProgToDelete(record);
    setIsDepLoading(true);
    setDepModalOpen(true);
    try {
      const response = await apiClient.get(`/api/v1/admin/programs/${record.id}/dependents`);
      setDepCounts(response.data);
    } catch (err) {
      message.error('Failed to query dependent entity counts.');
      setDepModalOpen(false);
    } finally {
      setIsDepLoading(false);
    }
  };

  // Confirm delete program
  const handleConfirmDeleteProg = () => {
    if (progToDelete) {
      deleteProgMutation.mutate(progToDelete.id);
    }
  };

  // Open Link Universities Modal
  const openLinkModal = (record) => {
    setSelectedProg(record);
    setLinkModalOpen(true);
  };

  // Handle University Link Checkbox toggle
  const handleLinkToggle = async (universityId, checked) => {
    try {
      if (checked) {
        await apiClient.post(`/api/v1/admin/programs/${selectedProg.id}/universities/${universityId}`);
        message.success('University linked successfully.');
        setLinkingUniIds((prev) => {
          const next = new Set(prev);
          next.add(universityId);
          return next;
        });
      } else {
        await apiClient.delete(`/api/v1/admin/programs/${selectedProg.id}/universities/${universityId}`);
        message.success('University unlinked successfully.');
        setLinkingUniIds((prev) => {
          const next = new Set(prev);
          next.delete(universityId);
          return next;
        });
      }
      queryClient.invalidateQueries({ queryKey: ['linkedUniversities', selectedProg.id] });
      queryClient.invalidateQueries({ queryKey: ['adminPrograms'] });
    } catch (error) {
      message.error(error.response?.data?.detail || 'Operation failed.');
    }
  };

  // Open Academic Tracks drawer
  const openTracksDrawer = (record) => {
    setSelectedProg(record);
    setTracksDrawerOpen(true);
  };

  // Handle Track Form Submit
  const handleTrackSubmit = (values) => {
    const payload = { ...values, study_program_id: selectedProg.id };
    if (editingTrack) {
      updateTrackMutation.mutate({ id: editingTrack.id, values: payload });
    } else {
      createTrackMutation.mutate(payload);
    }
  };

  // Open Edit Track Modal
  const showEditTrackModal = (record) => {
    setEditingTrack(record);
    setIsTrackFormDirty(false);
    trackForm.setFieldsValue({
      name: record.name,
      name_de: record.name_de,
      level: record.level,
      total_ects_required: record.total_ects_required,
      description: record.description,
      description_de: record.description_de,
      graduation_conditions: record.graduation_conditions,
      graduation_conditions_de: record.graduation_conditions_de,
    });
    setTracksModalOpen(true);
  };

  // Open Create Track Modal
  const showCreateTrackModal = () => {
    setEditingTrack(null);
    setIsTrackFormDirty(false);
    trackForm.resetFields();
    trackForm.setFieldsValue({ level: 'bachelor', total_ects_required: 180 });
    setTracksModalOpen(true);
  };

  const handleCancelTrackModal = () => {
    if (isTrackFormDirty) {
      Modal.confirm({
        title: 'Discard unsaved changes?',
        content: 'You have unsaved academic track changes. Are you sure you want to discard them?',
        okText: 'Yes, Discard',
        cancelText: 'No, Keep Editing',
        onOk: () => {
          setTracksModalOpen(false);
          setIsTrackFormDirty(false);
          trackForm.resetFields();
        },
      });
    } else {
      setTracksModalOpen(false);
      trackForm.resetFields();
    }
  };

  // Handle level change in track form to suggest ECTS defaults
  const handleTrackLevelChange = (level) => {
    let defaults = 180;
    if (level === 'master') defaults = 120;
    if (level === 'doctorate') defaults = 180;
    trackForm.setFieldsValue({ total_ects_required: defaults });
  };

  // Study Programs Columns definition
  const columns = [
    {
      title: 'Program Code',
      dataIndex: 'code',
      key: 'code',
      width: 140,
      render: (text) => <Tag color="purple">{text || '—'}</Tag>,
    },
    {
      title: lang === 'de' ? 'Studiengangsname' : 'Program Name',
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
      title: lang === 'de' ? 'Beschreibung' : 'Description',
      key: 'description',
      ellipsis: true,
      render: (_, record) => {
        return lang === 'de' ? (record.description_de || record.description || '—') : (record.description || record.description_de || '—');
      },
    },
    {
      title: 'Academic Tracks',
      key: 'tracks',
      width: 150,
      render: (_, record) => (
        <Button
          type="link"
          icon={<BranchesOutlined />}
          onClick={() => openTracksDrawer(record)}
        >
          {record.track_count ?? 0} Tracks
        </Button>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 200,
      render: (_, record) => (
        <Space size={8}>
          <Tooltip title="Link Universities">
            <Button
              type="text"
              icon={<LinkOutlined style={{ color: '#eb2f96' }} />}
              onClick={() => openLinkModal(record)}
            />
          </Tooltip>
          <Tooltip title="Edit Program Details">
            <Button
              type="text"
              icon={<EditOutlined style={{ color: '#1890ff' }} />}
              onClick={() => showEditProgModal(record)}
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
            <Tooltip title="Delete Program">
              <Button
                type="text"
                icon={<DeleteOutlined style={{ color: '#f5222d' }} />}
                onClick={() => showDeleteProgWarning(record)}
              />
            </Tooltip>
          ) : null}
        </Space>
      ),
    },
  ];

  // Academic Tracks Columns inside drawer
  const trackColumns = [
    {
      title: 'Track Level',
      dataIndex: 'level',
      key: 'level',
      width: 110,
      render: (text) => (
        <Tag color={text === 'master' ? 'cyan' : text === 'bachelor' ? 'blue' : 'gold'}>
          {text?.toUpperCase() || 'BACHELOR'}
        </Tag>
      ),
    },
    {
      title: 'Track Name',
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
      title: 'ECTS',
      dataIndex: 'total_ects_required',
      key: 'total_ects_required',
      width: 90,
      render: (text) => <Text strong>{text} ECTS</Text>,
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
            onClick={() => showEditTrackModal(record)}
          />
          <Popconfirm
            title="Delete Track?"
            description="Are you sure you want to delete this track?"
            okText="Yes"
            cancelText="No"
            onConfirm={() => deleteTrackMutation.mutate(record.id)}
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
            <Breadcrumb.Item>Study Programs</Breadcrumb.Item>
          </Breadcrumb>
          <Title level={2} style={{ margin: 0 }}>Study Programs</Title>
          <Paragraph style={{ margin: 0, marginTop: 4 }}>
            Create study programs (Filières), manage their corresponding academic tracks, and link them to active universities.
          </Paragraph>
        </div>

        {isSuperAdmin && (
          <Button type="primary" icon={<PlusOutlined />} onClick={showCreateProgModal}>
            Add Study Program
          </Button>
        )}
      </div>

      {/* Filter and Search Panel */}
      <Card style={{ marginBottom: 24, boxShadow: '0 1px 2px rgba(0,0,0,0.03)' }} bodyStyle={{ padding: '16px 24px' }}>
        <Row gutter={16}>
          <Col xs={24} md={12} lg={8}>
            <Input
              placeholder="Search programs by code or name..."
              prefix={<SearchOutlined style={{ color: '#bfbfbf' }} />}
              value={searchText}
              onChange={(e) => {
                const val = e.target.value;
                setSearchText(val);
                sessionStorage.setItem('programs_search', val);
                setCurrentPage(1);
                sessionStorage.setItem('programs_page', '1');
              }}
              allowClear
            />
          </Col>
          <Col xs={24} md={12} lg={16} style={{ textAlign: 'right' }}>
            <Button icon={<ReloadOutlined />} onClick={() => refetchProgs()}>
              Reload
            </Button>
          </Col>
        </Row>
      </Card>

      {/* Main Table */}
      <Table
        scroll={{ x: 'max-content' }}
        columns={columns}
        dataSource={progData?.programs || []}
        rowKey="id"
        loading={isProgLoading}
        pagination={{
          current: currentPage,
          pageSize: pageSize,
          total: progData?.total || 0,
          showSizeChanger: true,
          pageSizeOptions: ['5', '10', '20', '50'],
          onChange: (p, ps) => {
            setCurrentPage(p);
            sessionStorage.setItem('programs_page', String(p));
            setPageSize(ps);
          },
        }}
        locale={{
          emptyText: 'No study programs found matching criteria.',
        }}
      />

      {/* Program Add/Edit Modal */}
      <Modal
        title={editingProg ? 'Edit Study Program' : 'Register New Study Program'}
        open={progModalOpen}
        onCancel={handleCancelProgModal}
        footer={null}
        destroyOnClose
      >
        <Form
          form={progForm}
          layout="vertical"
          onFinish={handleProgSubmit}
          onValuesChange={() => setIsFormDirty(true)}
          style={{ marginTop: 16 }}
        >
          <Row gutter={16}>
            <Col span={16}>
              <Form.Item
                name="name"
                label="Program Name (English)"
                rules={[
                  { required: true, message: 'Please input the study program name' },
                  { max: 255, message: 'Must be 255 characters or less' },
                  germanTextRule,
                ]}
              >
                <Input placeholder="e.g. Computer Science" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="code"
                label="Code (Unique)"
                rules={[
                  { required: true, message: 'Code is required' },
                  { max: 50, message: 'Must be 50 characters or less' },
                  {
                    pattern: /^[A-Z0-9]+$/,
                    message: 'Uppercase letters and numbers only',
                  },
                ]}
              >
                <Input placeholder="e.g. CS" style={{ textTransform: 'uppercase' }} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="name_de"
            label="Program Name (German)"
            rules={[
              { max: 255, message: 'Must be 255 characters or less' },
              germanTextRule,
            ]}
          >
            <Input placeholder="e.g. Informatik" />
          </Form.Item>

          <Form.Item
            name="description"
            label="English Description"
            rules={[germanTextRule]}
          >
            <Input.TextArea rows={3} placeholder="Brief summary in English..." />
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
              <Button onClick={handleCancelProgModal}>Cancel</Button>
              <Button
                type="primary"
                htmlType="submit"
                loading={createProgMutation.isPending || updateProgMutation.isPending}
              >
                {editingProg ? 'Save Changes' : 'Create Program'}
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
        onOk={handleConfirmDeleteProg}
        okText="Yes, Soft-Delete Program"
        okButtonProps={{
          danger: true,
          loading: deleteProgMutation.isPending,
        }}
        confirmLoading={deleteProgMutation.isPending}
        destroyOnClose
      >
        <div style={{ marginTop: 16 }}>
          <Paragraph>
            Are you sure you want to delete study program <Text strong>{progToDelete?.name}</Text> ({progToDelete?.code})?
          </Paragraph>
          <Paragraph type="secondary">
            This action performs a soft deletion. It will mark the program and its associated academic tracks as deleted.
          </Paragraph>

          <Spin spinning={isDepLoading}>
            {depCounts && (
              <Card
                size="small"
                title="Dependent Entities Affected:"
                style={{ background: '#fff1f0', borderColor: '#ffa39e', marginTop: 16 }}
              >
                <ul style={{ paddingLeft: 20, margin: 0 }}>
                  <li>Linked Universities: <Text strong>{depCounts.universities ?? 0}</Text></li>
                  <li>Academic Tracks to delete: <Text strong>{depCounts.tracks ?? 0}</Text></li>
                  <li>Semesters: <Text strong>{depCounts.semesters ?? 0}</Text></li>
                  <li>Courses: <Text strong>{depCounts.courses ?? 0}</Text></li>
                </ul>
              </Card>
            )}
          </Spin>
        </div>
      </Modal>

      {/* University Linking Modal */}
      <Modal
        title={
          <Space>
            <LinkOutlined style={{ color: '#eb2f96' }} />
            <span>Link Universities to: {selectedProg?.name}</span>
          </Space>
        }
        open={linkModalOpen}
        onCancel={() => setLinkModalOpen(false)}
        footer={[
          <Button key="close" type="primary" onClick={() => setLinkModalOpen(false)}>
            Done
          </Button>,
        ]}
        destroyOnClose
      >
        <div style={{ marginTop: 16, maxHeight: 350, overflowY: 'auto' }}>
          <Paragraph type="secondary" style={{ marginBottom: 16 }}>
            Select which universities offer this study program.
          </Paragraph>

          <Spin spinning={isLinkedUnisLoading}>
            <Space direction="vertical" style={{ width: '100%' }} size={12}>
              {allUnisData?.universities?.map((uni) => (
                <Checkbox
                  key={uni.id}
                  checked={linkingUniIds.has(uni.id)}
                  disabled={!isSuperAdmin}
                  onChange={(e) => handleLinkToggle(uni.id, e.target.checked)}
                >
                  <Text strong>{uni.name}</Text> <Text type="secondary" style={{ fontSize: 11 }}>({uni.country})</Text>
                </Checkbox>
              ))}
              {allUnisData?.total === 0 && (
                <Text type="secondary">No universities registered in the system yet.</Text>
              )}
            </Space>
          </Spin>
        </div>
      </Modal>

      {/* Academic Tracks Drawer */}
      <Drawer
        title={`Academic Tracks: ${selectedProg?.name}`}
        placement="right"
        width={700}
        onClose={() => setTracksDrawerOpen(false)}
        open={tracksDrawerOpen}
        destroyOnClose
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <Text type="secondary">Configure specific degree tracks, levels, and ECTS requirements.</Text>
          {isSuperAdmin && (
            <Button type="primary" size="small" icon={<PlusOutlined />} onClick={showCreateTrackModal}>
              New Track
            </Button>
          )}
        </div>

        <Table
          columns={trackColumns}
          dataSource={tracksData?.tracks || []}
          rowKey="id"
          loading={isTracksLoading}
          pagination={false}
          locale={{
            emptyText: 'No academic tracks registered for this study program.',
          }}
        />
      </Drawer>

      {/* Academic Track Modal */}
      <Modal
        title={editingTrack ? 'Edit Academic Track' : 'Create Academic Track'}
        open={tracksModalOpen}
        onCancel={handleCancelTrackModal}
        footer={null}
        destroyOnClose
      >
        <Form
          form={trackForm}
          layout="vertical"
          onFinish={handleTrackSubmit}
          onValuesChange={() => setIsTrackFormDirty(true)}
          style={{ marginTop: 16 }}
        >
          <Row gutter={16}>
            <Col span={14}>
              <Form.Item
                name="name"
                label="Track Name (English)"
                rules={[
                  { required: true, message: 'Please input the track name' },
                  { max: 255, message: 'Must be 255 characters or less' },
                  germanTextRule,
                ]}
              >
                <Input placeholder="e.g. Software Engineering Track" />
              </Form.Item>
            </Col>
            <Col span={10}>
              <Form.Item
                name="level"
                label="Degree Level"
                rules={[{ required: true, message: 'Degree level is required' }]}
              >
                <Select onChange={handleTrackLevelChange}>
                  <Option value="bachelor">Bachelor</Option>
                  <Option value="master">Master</Option>
                  <Option value="doctorate">Doctorate</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="name_de"
            label="Track Name (German)"
            rules={[
              { max: 255, message: 'Must be 255 characters or less' },
              germanTextRule,
            ]}
          >
            <Input placeholder="e.g. Softwaretechnik" />
          </Form.Item>

          <Form.Item
            name="total_ects_required"
            label="Total Graduation ECTS Credits"
            rules={[
              { required: true, message: 'ECTS requirement is required' },
              {
                validator: (_, value) => {
                  if (value && (isNaN(value) || parseInt(value) <= 0)) {
                    return Promise.reject(new Error('ECTS credits must be a positive number'));
                  }
                  return Promise.resolve();
                },
              },
            ]}
          >
            <Input type="number" min={1} placeholder="e.g. 180" />
          </Form.Item>

          <Form.Item
            name="description"
            label="English Description"
            rules={[germanTextRule]}
          >
            <Input.TextArea rows={3} placeholder="Details about graduation criteria..." />
          </Form.Item>

          <Form.Item
            name="description_de"
            label="German Description"
            rules={[germanTextRule]}
          >
            <Input.TextArea rows={3} placeholder="Zusatzinformationen..." />
          </Form.Item>

          <Form.Item
            name="graduation_conditions"
            label="English Graduation Conditions"
            rules={[germanTextRule]}
          >
            <Input.TextArea rows={2} placeholder="e.g. Completion of thesis and internship" />
          </Form.Item>

          <Form.Item
            name="graduation_conditions_de"
            label="German Graduation Conditions"
            rules={[germanTextRule]}
          >
            <Input.TextArea rows={2} placeholder="Zulassungsbedingungen zum Abschluss..." />
          </Form.Item>

          <Form.Item style={{ textAlign: 'right', marginBottom: 0, marginTop: 24 }}>
            <Space>
              <Button onClick={handleCancelTrackModal}>Cancel</Button>
              <Button
                type="primary"
                htmlType="submit"
                loading={createTrackMutation.isPending || updateTrackMutation.isPending}
              >
                {editingTrack ? 'Save Track' : 'Create Track'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* History Drawer */}
      <Drawer
        title="Study Program Change History"
        placement="right"
        width={480}
        onClose={() => {
          setHistoryDrawerOpen(false);
          setHistoryEntityId(null);
        }}
        open={historyDrawerOpen}
        destroyOnClose
      >
        <EntityHistory entityType="study_program" entityId={historyEntityId} />
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

export default StudyPrograms;
