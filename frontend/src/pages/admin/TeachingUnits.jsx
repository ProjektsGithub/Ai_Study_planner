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

const TeachingUnits = () => {
  const queryClient = useQueryClient();
  const { hasRole } = useAuth();
  const isSuperAdmin = hasRole('super_admin');
  const { lang } = useLanguage();

  // Filters and table state
  const [searchText, setSearchText] = useState(() => sessionStorage.getItem('units_search') || '');
  const [selectedTrackId, setSelectedTrackId] = useState(() => sessionStorage.getItem('units_track_id') || undefined);
  const [selectedSemesterId, setSelectedSemesterId] = useState(() => sessionStorage.getItem('units_semester_id') || undefined);
  const [currentPage, setCurrentPage] = useState(() => {
    const val = sessionStorage.getItem('units_page');
    return val ? parseInt(val, 10) : 1;
  });
  const [pageSize, setPageSize] = useState(10);

  // Form Modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [editingUnit, setEditingUnit] = useState(null);
  const [unitForm] = Form.useForm();

  // Deletion modal state
  const [depModalOpen, setDepModalOpen] = useState(false);
  const [unitToDelete, setUnitToDelete] = useState(null);
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

  // 1. Fetch academic tracks for mappings and filters
  const { data: trackListData } = useQuery({
    queryKey: ['allTracksList'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/admin/tracks?limit=200');
      return response.data;
    },
  });

  // 2. Fetch semesters for selectors and mapping
  const { data: semesterListData } = useQuery({
    queryKey: ['allSemestersList'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/admin/semesters?limit=1000');
      return response.data;
    },
  });

  // 3. Fetch teaching units
  const {
    data: unitListData,
    isLoading: isUnitLoading,
    refetch: refetchUnits,
  } = useQuery({
    queryKey: ['adminTeachingUnitsGlobal', currentPage, pageSize, searchText, selectedTrackId, selectedSemesterId],
    queryFn: async () => {
      const skip = (currentPage - 1) * pageSize;
      const params = { skip, limit: pageSize };
      if (searchText) params.search = searchText;
      if (selectedTrackId) params.academic_track_id = selectedTrackId;
      if (selectedSemesterId) params.semester_id = selectedSemesterId;

      const response = await apiClient.get('/api/v1/admin/teaching-units', { params });
      return response.data;
    },
  });

  // 4. Mutations
  const createUnitMutation = useMutation({
    mutationFn: async (values) => {
      const response = await apiClient.post('/api/v1/admin/teaching-units', values);
      return response.data;
    },
    onSuccess: () => {
      message.success('Teaching unit created successfully.');
      setIsFormDirty(false);
      setModalOpen(false);
      unitForm.resetFields();
      queryClient.invalidateQueries({ queryKey: ['adminTeachingUnitsGlobal'] });
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || 'Failed to create teaching unit.');
    },
  });

  const updateUnitMutation = useMutation({
    mutationFn: async ({ id, values }) => {
      const response = await apiClient.put(`/api/v1/admin/teaching-units/${id}`, values);
      return response.data;
    },
    onSuccess: () => {
      message.success('Teaching unit updated successfully.');
      setIsFormDirty(false);
      setModalOpen(false);
      setEditingUnit(null);
      unitForm.resetFields();
      queryClient.invalidateQueries({ queryKey: ['adminTeachingUnitsGlobal'] });
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || 'Failed to update teaching unit.');
    },
  });

  const deleteUnitMutation = useMutation({
    mutationFn: async (id) => {
      const response = await apiClient.delete(`/api/v1/admin/teaching-units/${id}`);
      return response.data;
    },
    onSuccess: () => {
      message.success('Teaching unit soft-deleted successfully.');
      setDepModalOpen(false);
      setUnitToDelete(null);
      setDepCounts(null);
      queryClient.invalidateQueries({ queryKey: ['adminTeachingUnitsGlobal'] });
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || 'Failed to delete teaching unit.');
    },
  });

  // Maps
  const trackMap = {};
  trackListData?.tracks?.forEach((t) => {
    trackMap[t.id] = t;
  });

  const semesterMap = {};
  semesterListData?.semesters?.forEach((s) => {
    semesterMap[s.id] = s;
  });

  const handleFormSubmit = (values) => {
    const payload = {
      ...values,
      ects_required: values.ects_required ? parseInt(values.ects_required, 10) : 0,
    };
    if (editingUnit) {
      updateUnitMutation.mutate({ id: editingUnit.id, values: payload });
    } else {
      createUnitMutation.mutate(payload);
    }
  };

  const showCreateModal = () => {
    setEditingUnit(null);
    setIsFormDirty(false);
    unitForm.resetFields();
    unitForm.setFieldsValue({ ects_required: 0 });
    setModalOpen(true);
  };

  const showEditModal = (record) => {
    setEditingUnit(record);
    setIsFormDirty(false);
    unitForm.setFieldsValue({
      semester_id: record.semester_id,
      name: record.name,
      name_de: record.name_de,
      code: record.code,
      ects_required: record.ects_required,
      description: record.description,
      description_de: record.description_de,
    });
    setModalOpen(true);
  };

  const handleCancelUnitModal = () => {
    if (isFormDirty) {
      Modal.confirm({
        title: 'Discard unsaved changes?',
        content: 'You have unsaved teaching unit changes. Are you sure you want to discard them?',
        okText: 'Yes, Discard',
        cancelText: 'No, Keep Editing',
        onOk: () => {
          setModalOpen(false);
          setIsFormDirty(false);
          unitForm.resetFields();
        },
      });
    } else {
      setModalOpen(false);
      unitForm.resetFields();
    }
  };

  const showDeleteWarning = async (record) => {
    setUnitToDelete(record);
    setIsDepLoading(true);
    setDepModalOpen(true);
    try {
      const response = await apiClient.get(`/api/v1/admin/teaching-units/${record.id}/dependents`);
      setDepCounts(response.data);
    } catch (err) {
      message.error('Failed to query dependent counts.');
      setDepModalOpen(false);
    } finally {
      setIsDepLoading(false);
    }
  };

  const handleConfirmDelete = () => {
    if (unitToDelete) {
      deleteUnitMutation.mutate(unitToDelete.id);
    }
  };

  const columns = [
    {
      title: 'Code',
      dataIndex: 'code',
      key: 'code',
      width: 120,
      render: (code) => code ? <Tag color="purple" style={{ fontWeight: 'bold' }}>{code}</Tag> : '—',
    },
    {
      title: lang === 'de' ? 'Name der Lerneinheit' : 'Teaching Unit Name',
      key: 'unit_name',
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
      title: lang === 'de' ? 'Semester / Studienrichtung' : 'Semester / Track',
      key: 'semester_track',
      render: (_, record) => {
        const sem = semesterMap[record.semester_id];
        const track = sem ? trackMap[sem.academic_track_id] : null;
        if (!sem) return '—';
        const semName = lang === 'de' ? (sem.name_de || sem.name) : (sem.name || sem.name_de);
        const trackName = track ? (lang === 'de' ? (track.name_de || track.name) : (track.name || track.name_de)) : '';
        return (
          <Space direction="vertical" size={0}>
            <Text style={{ fontSize: 13 }}>{semName} (S{sem.semester_number})</Text>
            {trackName && (
              <Text type="secondary" style={{ fontSize: 11 }}>
                {lang === 'de' ? 'Studienrichtung: ' : 'Track: '}{trackName}
              </Text>
            )}
          </Space>
        );
      },
    },
    {
      title: 'ECTS Required',
      dataIndex: 'ects_required',
      key: 'ects_required',
      width: 140,
      render: (ects) => <Text strong>{ects ?? 0} ECTS</Text>,
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 120,
      render: (_, record) => (
        <Space size={8}>
          <Tooltip title="Edit Teaching Unit">
            <Button
              type="text"
              icon={<EditOutlined style={{ color: '#1890ff' }} />}
              onClick={() => showEditModal(record)}
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
            <Tooltip title="Delete Teaching Unit">
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
            <Breadcrumb.Item>Teaching Units</Breadcrumb.Item>
          </Breadcrumb>
          <Title level={2} style={{ margin: 0 }}>Teaching Units (UE)</Title>
          <Paragraph style={{ margin: 0, marginTop: 4 }}>
            Manage Unités d'Enseignement (UE) modules, required ECTS benchmarks, and link them to semesters.
          </Paragraph>
        </div>

        {isSuperAdmin && (
          <Button type="primary" icon={<PlusOutlined />} onClick={showCreateModal}>
            Add Teaching Unit
          </Button>
        )}
      </div>

      {/* Filter panel */}
      <Card style={{ marginBottom: 24, boxShadow: '0 1px 2px rgba(0,0,0,0.03)' }} bodyStyle={{ padding: '16px 24px' }}>
        <Row gutter={16} align="middle">
          <Col xs={24} md={8}>
            <Input
              placeholder="Search units by code or name..."
              prefix={<SearchOutlined style={{ color: '#bfbfbf' }} />}
              value={searchText}
              onChange={(e) => {
                const val = e.target.value;
                setSearchText(val);
                sessionStorage.setItem('units_search', val);
                setCurrentPage(1);
                sessionStorage.setItem('units_page', '1');
              }}
              allowClear
            />
          </Col>
          <Col xs={24} md={6}>
            <Select
              style={{ width: '100%' }}
              placeholder="Filter by Academic Track"
              value={selectedTrackId}
              onChange={(val) => {
                setSelectedTrackId(val || undefined);
                if (val) {
                  sessionStorage.setItem('units_track_id', val);
                } else {
                  sessionStorage.removeItem('units_track_id');
                }
                setSelectedSemesterId(undefined); // reset dependent filter
                sessionStorage.removeItem('units_semester_id');
                setCurrentPage(1);
                sessionStorage.setItem('units_page', '1');
              }}
              allowClear
            >
              {trackListData?.tracks?.map((track) => (
                <Option key={track.id} value={track.id}>
                  {track.name} ({track.level})
                </Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} md={6}>
            <Select
              style={{ width: '100%' }}
              placeholder="Filter by Semester"
              value={selectedSemesterId}
              onChange={(val) => {
                setSelectedSemesterId(val || undefined);
                if (val) {
                  sessionStorage.setItem('units_semester_id', val);
                } else {
                  sessionStorage.removeItem('units_semester_id');
                }
                setCurrentPage(1);
                sessionStorage.setItem('units_page', '1');
              }}
              allowClear
              disabled={!selectedTrackId}
            >
              {semesterListData?.semesters
                ?.filter((s) => !selectedTrackId || s.academic_track_id === selectedTrackId)
                ?.map((sem) => (
                  <Option key={sem.id} value={sem.id}>
                    {sem.name} (S{sem.semester_number})
                  </Option>
                ))}
            </Select>
          </Col>
          <Col xs={24} md={4} style={{ textAlign: 'right' }}>
            <Button icon={<ReloadOutlined />} onClick={() => refetchUnits()}>
              Reload
            </Button>
          </Col>
        </Row>
      </Card>

      {/* Main Table */}
      <Table
        scroll={{ x: 'max-content' }}
        columns={columns}
        dataSource={unitListData?.teaching_units || []}
        rowKey="id"
        loading={isUnitLoading}
        pagination={{
          current: currentPage,
          pageSize: pageSize,
          total: unitListData?.total || 0,
          showSizeChanger: true,
          pageSizeOptions: ['5', '10', '20', '50'],
          onChange: (p, ps) => {
            setCurrentPage(p);
            sessionStorage.setItem('units_page', String(p));
            setPageSize(ps);
          },
        }}
        locale={{
          emptyText: 'No teaching units found matching criteria.',
        }}
      />

      {/* Add/Edit Modal */}
      <Modal
        title={editingUnit ? 'Edit Teaching Unit' : 'Create Teaching Unit'}
        open={modalOpen}
        onCancel={handleCancelUnitModal}
        footer={null}
        destroyOnClose
      >
        <Form
          form={unitForm}
          layout="vertical"
          onFinish={handleFormSubmit}
          onValuesChange={() => setIsFormDirty(true)}
          style={{ marginTop: 16 }}
        >
          <Form.Item
            name="semester_id"
            label="Belongs to Semester"
            rules={[{ required: true, message: 'Please select a parent semester' }]}
          >
            <Select placeholder="Select semester...">
              {semesterListData?.semesters?.map((sem) => {
                const track = trackMap[sem.academic_track_id];
                return (
                  <Option key={sem.id} value={sem.id}>
                    {sem.name} (S{sem.semester_number}) — Track: {track?.name || '—'}
                  </Option>
                );
              })}
            </Select>
          </Form.Item>

          <Row gutter={16}>
            <Col span={16}>
              <Form.Item
                name="name"
                label="Teaching Unit Name (English)"
                rules={[
                  { required: true, message: 'Please input the teaching unit name' },
                  { max: 255, message: 'Must be 255 characters or less' },
                  germanTextRule,
                ]}
              >
                <Input placeholder="e.g. Fundamental Mathematics" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="code"
                label="Code"
                rules={[
                  { required: true, message: 'Please input the teaching unit code' },
                  { max: 50, message: 'Must be 50 characters or less' },
                  {
                    pattern: /^[A-Z0-9]+$/,
                    message: 'Uppercase letters and numbers only',
                  },
                ]}
              >
                <Input placeholder="e.g. UE1" style={{ textTransform: 'uppercase' }} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="name_de"
            label="Teaching Unit Name (German)"
            rules={[
              { max: 255, message: 'Must be 255 characters or less' },
              germanTextRule,
            ]}
          >
            <Input placeholder="e.g. Grundlagen der Mathematik" />
          </Form.Item>

          <Form.Item
            name="ects_required"
            label="ECTS Required for this Unit"
            rules={[
              { required: true, message: 'Please input required ECTS credits' },
              {
                validator: (_, value) => {
                  if (value !== undefined && value !== null && (isNaN(value) || parseInt(value, 10) < 0)) {
                    return Promise.reject(new Error('ECTS credits must be a non-negative number'));
                  }
                  return Promise.resolve();
                },
              },
            ]}
          >
            <Input type="number" min={0} placeholder="e.g. 12" />
          </Form.Item>

          <Form.Item
            name="description"
            label="English Description"
            rules={[germanTextRule]}
          >
            <Input.TextArea rows={3} placeholder="Objectives, standard components of this UE..." />
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
              <Button onClick={handleCancelUnitModal}>Cancel</Button>
              <Button
                type="primary"
                htmlType="submit"
                loading={createUnitMutation.isPending || updateUnitMutation.isPending}
              >
                {editingUnit ? 'Save Changes' : 'Create Unit'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* Deletion Impact Warning Modal */}
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
        okText="Yes, Soft-Delete Teaching Unit"
        okButtonProps={{
          danger: true,
          loading: deleteUnitMutation.isPending,
          disabled: depCounts && depCounts.courses_count > 0, // Block if has linked courses
        }}
        confirmLoading={deleteUnitMutation.isPending}
        destroyOnClose
      >
        <div style={{ marginTop: 16 }}>
          <Paragraph>
            Are you sure you want to delete teaching unit <Text strong>{unitToDelete?.name}</Text>?
          </Paragraph>
          <Paragraph type="secondary">
            This action performs a soft deletion. It will mark the teaching unit as deleted in the database.
          </Paragraph>

          <Spin spinning={isDepLoading}>
            {depCounts && (
              <Card
                size="small"
                title="Dependent Entities Affected:"
                style={{
                  background: depCounts.courses_count > 0 ? '#fff2e8' : '#fff1f0',
                  borderColor: depCounts.courses_count > 0 ? '#ffbb96' : '#ffa39e',
                  marginTop: 16
                }}
              >
                <ul style={{ paddingLeft: 20, margin: 0 }}>
                  <li>Courses linked to this UE: <Text strong>{depCounts.courses_count ?? 0}</Text></li>
                </ul>

                {depCounts.courses_count > 0 && (
                  <div style={{ marginTop: 12, color: '#d4380d', fontWeight: 'bold' }}>
                    <WarningOutlined /> Deletion is BLOCKED because there are active courses assigned to this teaching unit. You must delete or re-assign the courses first.
                  </div>
                )}
              </Card>
            )}
          </Spin>
        </div>
      </Modal>

      {/* History Drawer */}
      <Drawer
        title="Teaching Unit Change History"
        placement="right"
        width={480}
        onClose={() => {
          setHistoryDrawerOpen(false);
          setHistoryEntityId(null);
        }}
        open={historyDrawerOpen}
        destroyOnClose
      >
        <EntityHistory entityType="teaching_unit" entityId={historyEntityId} />
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

export default TeachingUnits;
