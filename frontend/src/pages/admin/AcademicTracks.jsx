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
  Select,
  Tag,
  Spin,
  Tooltip,
  Drawer,
  message,
} from 'antd';
import {
  BranchesOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SearchOutlined,
  ReloadOutlined,
  WarningOutlined,
  HistoryOutlined,
} from '@ant-design/icons';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';

const { Title, Paragraph, Text } = Typography;
const { Option } = Select;

const AcademicTracks = () => {
  const queryClient = useQueryClient();
  const { hasRole } = useAuth();
  const isSuperAdmin = hasRole('super_admin');
  const { lang } = useLanguage();

  // Table filtering and search states
  const [searchText, setSearchText] = useState(() => sessionStorage.getItem('tracks_search') || '');
  const [selectedProgramId, setSelectedProgramId] = useState(() => sessionStorage.getItem('tracks_program_id') || undefined);
  const [selectedLevel, setSelectedLevel] = useState(() => sessionStorage.getItem('tracks_level') || undefined);
  const [currentPage, setCurrentPage] = useState(() => {
    const val = sessionStorage.getItem('tracks_page');
    return val ? parseInt(val, 10) : 1;
  });
  const [pageSize, setPageSize] = useState(10);

  // Track Form Modal states
  const [trackModalOpen, setTrackModalOpen] = useState(false);
  const [editingTrack, setEditingTrack] = useState(null);
  const [trackForm] = Form.useForm();

  // Deletion dependents state
  const [depModalOpen, setDepModalOpen] = useState(false);
  const [trackToDelete, setTrackToDelete] = useState(null);
  const [depCounts, setDepCounts] = useState(null);
  const [isDepLoading, setIsDepLoading] = useState(false);

  // History Drawer states
  const [historyDrawerOpen, setHistoryDrawerOpen] = useState(false);
  const [historyEntityId, setHistoryEntityId] = useState(null);

  // Dirty form state
  const [isFormDirty, setIsFormDirty] = useState(false);

  const blocker = useBlocker(
    ({ currentValue, nextLocation }) =>
      isFormDirty && currentValue.pathname !== nextLocation.pathname
  );

  const germanTextRule = {
    pattern: /^[a-zA-ZäöüßÄÖÜ0-9\s\.,\-\(\)\/\':;&\!?%@#\+\*\[\]]*$/,
    message: 'Invalid characters. German letters (ä, ö, ü, ß) and common punctuation are supported.',
  };

  // Fetch all study programs for form selectors and filters
  const { data: programData } = useQuery({
    queryKey: ['allProgramsList'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/admin/programs?limit=200');
      return response.data;
    },
  });

  // 1. Fetch academic tracks (paginated and filtered)
  const {
    data: trackData,
    isLoading: isTrackLoading,
    refetch: refetchTracks,
  } = useQuery({
    queryKey: ['adminTracksGlobal', currentPage, pageSize, searchText, selectedProgramId, selectedLevel],
    queryFn: async () => {
      const skip = (currentPage - 1) * pageSize;
      const params = { skip, limit: pageSize };
      if (searchText) params.search = searchText;
      if (selectedProgramId) params.study_program_id = selectedProgramId;
      if (selectedLevel) params.level = selectedLevel;

      const response = await apiClient.get('/api/v1/admin/tracks', { params });
      return response.data;
    },
  });

  // 2. Mutations for tracks CRUD
  const createTrackMutation = useMutation({
    mutationFn: async (values) => {
      const response = await apiClient.post('/api/v1/admin/tracks', values);
      return response.data;
    },
    onSuccess: () => {
      message.success('Academic track created successfully.');
      setIsFormDirty(false);
      setTrackModalOpen(false);
      trackForm.resetFields();
      queryClient.invalidateQueries({ queryKey: ['adminTracksGlobal'] });
      queryClient.invalidateQueries({ queryKey: ['adminPrograms'] }); // Refresh program track counts
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
      setIsFormDirty(false);
      setTrackModalOpen(false);
      setEditingTrack(null);
      trackForm.resetFields();
      queryClient.invalidateQueries({ queryKey: ['adminTracksGlobal'] });
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
      setDepModalOpen(false);
      setTrackToDelete(null);
      setDepCounts(null);
      queryClient.invalidateQueries({ queryKey: ['adminTracksGlobal'] });
      queryClient.invalidateQueries({ queryKey: ['adminPrograms'] });
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || 'Failed to delete academic track.');
    },
  });

  // Handle Level change defaults
  const handleLevelChange = (level) => {
    let defaults = 180;
    if (level === 'master') defaults = 120;
    if (level === 'doctorate') defaults = 180;
    trackForm.setFieldsValue({ total_ects_required: defaults });
  };

  // Submit track form
  const handleTrackSubmit = (values) => {
    const payload = {
      ...values,
      total_ects_required: parseInt(values.total_ects_required),
    };
    if (editingTrack) {
      updateTrackMutation.mutate({ id: editingTrack.id, values: payload });
    } else {
      createTrackMutation.mutate(payload);
    }
  };

  // Open edit modal
  const showEditTrackModal = (record) => {
    setEditingTrack(record);
    setIsFormDirty(false);
    trackForm.setFieldsValue({
      study_program_id: record.study_program_id,
      name: record.name,
      name_de: record.name_de,
      level: record.level,
      total_ects_required: record.total_ects_required,
      description: record.description,
      description_de: record.description_de,
      graduation_conditions: record.graduation_conditions,
      graduation_conditions_de: record.graduation_conditions_de,
    });
    setTrackModalOpen(true);
  };

  // Open create modal
  const showCreateTrackModal = () => {
    setEditingTrack(null);
    setIsFormDirty(false);
    trackForm.resetFields();
    trackForm.setFieldsValue({ level: 'bachelor', total_ects_required: 180 });
    setTrackModalOpen(true);
  };

  const handleCancelTrackModal = () => {
    if (isFormDirty) {
      Modal.confirm({
        title: 'Discard unsaved changes?',
        content: 'You have unsaved academic track changes. Are you sure you want to discard them?',
        okText: 'Yes, Discard',
        cancelText: 'No, Keep Editing',
        onOk: () => {
          setTrackModalOpen(false);
          setIsFormDirty(false);
          trackForm.resetFields();
        },
      });
    } else {
      setTrackModalOpen(false);
      trackForm.resetFields();
    }
  };

  // Dependents delete check warning
  const showDeleteWarning = async (record) => {
    setTrackToDelete(record);
    setIsDepLoading(true);
    setDepModalOpen(true);
    try {
      const response = await apiClient.get(`/api/v1/admin/tracks/${record.id}/dependents`);
      setDepCounts(response.data);
    } catch (err) {
      message.error('Failed to query dependent entity counts.');
      setDepModalOpen(false);
    } finally {
      setIsDepLoading(false);
    }
  };

  const handleConfirmDelete = () => {
    if (trackToDelete) {
      deleteTrackMutation.mutate(trackToDelete.id);
    }
  };

  // Map programs list to index map
  const programMap = {};
  programData?.programs?.forEach((p) => {
    programMap[p.id] = p;
  });

  const columns = [
    {
      title: 'Degree Level',
      dataIndex: 'level',
      key: 'level',
      width: 130,
      render: (level) => (
        <Tag color={level === 'master' ? 'cyan' : level === 'bachelor' ? 'blue' : 'gold'}>
          {level?.toUpperCase() || 'BACHELOR'}
        </Tag>
      ),
    },
    {
      title: lang === 'de' ? 'Name der Studienrichtung' : 'Track Name',
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
      title: lang === 'de' ? 'Studiengang' : 'Study Program',
      key: 'program',
      width: 200,
      render: (_, record) => {
        const prog = programMap[record.study_program_id];
        if (!prog) return '—';
        const progName = lang === 'de' ? (prog.name_de || prog.name) : (prog.name || prog.name_de);
        return (
          <Space direction="vertical" size={0}>
            <Text style={{ fontSize: 13 }}>{progName}</Text>
            <Tag color="purple" style={{ fontSize: 11, margin: 0 }}>{prog.code}</Tag>
          </Space>
        );
      },
    },
    {
      title: 'ECTS Required',
      dataIndex: 'total_ects_required',
      key: 'total_ects_required',
      width: 140,
      render: (ects) => <Text strong>{ects} ECTS</Text>,
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 120,
      render: (_, record) => (
        <Space size={8}>
          <Tooltip title="Edit Track Details">
            <Button
              type="text"
              icon={<EditOutlined style={{ color: '#1890ff' }} />}
              onClick={() => showEditTrackModal(record)}
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
          {isSuperAdmin && (
            <Tooltip title="Delete Track">
              <Button
                type="text"
                icon={<DeleteOutlined style={{ color: '#f5222d' }} />}
                onClick={() => showDeleteWarning(record)}
              />
            </Tooltip>
          )}
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
            <Breadcrumb.Item>Academic Tracks</Breadcrumb.Item>
          </Breadcrumb>
          <Title level={2} style={{ margin: 0 }}>Academic Tracks</Title>
          <Paragraph style={{ margin: 0, marginTop: 4 }}>
            Configure degree levels, graduation ECTS limits, conditions, and course semesters.
          </Paragraph>
        </div>

        {isSuperAdmin && (
          <Button type="primary" icon={<PlusOutlined />} onClick={showCreateTrackModal}>
            Add Academic Track
          </Button>
        )}
      </div>

      {/* Filter and Search Panel */}
      <Card style={{ marginBottom: 24, boxShadow: '0 1px 2px rgba(0,0,0,0.03)' }} bodyStyle={{ padding: '16px 24px' }}>
        <Row gutter={16} align="middle">
          <Col xs={24} md={8}>
            <Input
              placeholder="Search tracks by name..."
              prefix={<SearchOutlined style={{ color: '#bfbfbf' }} />}
              value={searchText}
              onChange={(e) => {
                const val = e.target.value;
                setSearchText(val);
                sessionStorage.setItem('tracks_search', val);
                setCurrentPage(1);
                sessionStorage.setItem('tracks_page', '1');
              }}
              allowClear
            />
          </Col>
          <Col xs={24} md={6}>
            <Select
              style={{ width: '100%' }}
              placeholder="Filter by Study Program"
              value={selectedProgramId}
              onChange={(val) => {
                setSelectedProgramId(val || undefined);
                if (val) {
                  sessionStorage.setItem('tracks_program_id', val);
                } else {
                  sessionStorage.removeItem('tracks_program_id');
                }
                setCurrentPage(1);
                sessionStorage.setItem('tracks_page', '1');
              }}
              allowClear
            >
              {programData?.programs?.map((prog) => (
                <Option key={prog.id} value={prog.id}>
                  {prog.name} ({prog.code})
                </Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} md={6}>
            <Select
              style={{ width: '100%' }}
              placeholder="Filter by Level"
              value={selectedLevel}
              onChange={(val) => {
                setSelectedLevel(val || undefined);
                if (val) {
                  sessionStorage.setItem('tracks_level', val);
                } else {
                  sessionStorage.removeItem('tracks_level');
                }
                setCurrentPage(1);
                sessionStorage.setItem('tracks_page', '1');
              }}
              allowClear
            >
              <Option value="bachelor">Bachelor</Option>
              <Option value="master">Master</Option>
              <Option value="doctorate">Doctorate</Option>
            </Select>
          </Col>
          <Col xs={24} md={4} style={{ textAlign: 'right' }}>
            <Button icon={<ReloadOutlined />} onClick={() => refetchTracks()}>
              Reload
            </Button>
          </Col>
        </Row>
      </Card>

      {/* Main Table */}
      <Table
        scroll={{ x: 'max-content' }}
        columns={columns}
        dataSource={trackData?.tracks || []}
        rowKey="id"
        loading={isTrackLoading}
        pagination={{
          current: currentPage,
          pageSize: pageSize,
          total: trackData?.total || 0,
          showSizeChanger: true,
          pageSizeOptions: ['5', '10', '20', '50'],
          onChange: (p, ps) => {
            setCurrentPage(p);
            sessionStorage.setItem('tracks_page', String(p));
            setPageSize(ps);
          },
        }}
        locale={{
          emptyText: 'No academic tracks found matching criteria.',
        }}
      />

      {/* Add/Edit Modal */}
      <Modal
        title={editingTrack ? 'Edit Academic Track' : 'Create Academic Track'}
        open={trackModalOpen}
        onCancel={handleCancelTrackModal}
        footer={null}
        destroyOnClose
      >
        <Form
          form={trackForm}
          layout="vertical"
          onFinish={handleTrackSubmit}
          onValuesChange={() => setIsFormDirty(true)}
          style={{ marginTop: 16 }}
        >
          <Form.Item
            name="study_program_id"
            label="Belongs to Study Program"
            rules={[{ required: true, message: 'Please select a parent study program' }]}
          >
            <Select placeholder="Select program...">
              {programData?.programs?.map((prog) => (
                <Option key={prog.id} value={prog.id}>
                  {prog.name} ({prog.code})
                </Option>
              ))}
            </Select>
          </Form.Item>

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
                rules={[{ required: true, message: 'Please select degree level' }]}
              >
                <Select onChange={handleLevelChange}>
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
              { required: true, message: 'ECTS credits count is required' },
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
            <Input.TextArea rows={3} placeholder="Provide details about the track goals..." />
          </Form.Item>

          <Form.Item
            name="description_de"
            label="German Description"
            rules={[germanTextRule]}
          >
            <Input.TextArea rows={3} placeholder="Beschreibung auf Deutsch..." />
          </Form.Item>

          <Form.Item
            name="graduation_conditions"
            label="English Graduation Conditions"
            rules={[germanTextRule]}
          >
            <Input.TextArea rows={2} placeholder="Thesis defense, minimum internship hours, etc." />
          </Form.Item>

          <Form.Item
            name="graduation_conditions_de"
            label="German Graduation Conditions"
            rules={[germanTextRule]}
          >
            <Input.TextArea rows={2} placeholder="Abschlussbedingungen auf Deutsch..." />
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

      {/* Deletion Warning Modal */}
      <Modal
        title={
          <Space>
            <WarningOutlined style={{ color: '#f5222d' }} />
            <span>Confirm Deletion Impact</span>
          </Space>
        }
        open={depModalOpen}
        onCancel={() => setDepModalOpen(false)}
        onOk={handleConfirmDelete}
        okText="Yes, Soft-Delete Track"
        okButtonProps={{
          danger: true,
          loading: deleteTrackMutation.isPending,
        }}
        confirmLoading={deleteTrackMutation.isPending}
        destroyOnClose
      >
        <div style={{ marginTop: 16 }}>
          <Paragraph>
            Are you sure you want to delete academic track <Text strong>{trackToDelete?.name}</Text>?
          </Paragraph>
          <Paragraph type="secondary">
            This action performs a soft deletion. It will mark the track and its associated semesters as deleted.
          </Paragraph>

          <Spin spinning={isDepLoading}>
            {depCounts && (
              <Card
                size="small"
                title="Dependent Entities Affected:"
                style={{ background: '#fff1f0', borderColor: '#ffa39e', marginTop: 16 }}
              >
                <ul style={{ paddingLeft: 20, margin: 0 }}>
                  <li>Semesters to delete: <Text strong>{depCounts.semesters_count ?? 0}</Text></li>
                  <li>Courses affected: <Text strong>{depCounts.courses_count ?? 0}</Text></li>
                </ul>
              </Card>
            )}
          </Spin>
        </div>
      </Modal>

      {/* History Drawer */}
      <Drawer
        title="Academic Track Change History"
        placement="right"
        width={480}
        onClose={() => {
          setHistoryDrawerOpen(false);
          setHistoryEntityId(null);
        }}
        open={historyDrawerOpen}
        destroyOnClose
      >
        <EntityHistory entityType="academic_track" entityId={historyEntityId} />
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

export default AcademicTracks;
