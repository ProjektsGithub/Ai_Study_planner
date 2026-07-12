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

const Semesters = () => {
  const queryClient = useQueryClient();
  const { hasRole } = useAuth();
  const isSuperAdmin = hasRole('super_admin');
  const { lang } = useLanguage();

  // Filters and table state
  const [searchText, setSearchText] = useState(() => sessionStorage.getItem('semesters_search') || '');
  const [selectedTrackId, setSelectedTrackId] = useState(() => sessionStorage.getItem('semesters_track_id') || undefined);
  const [selectedSemesterNum, setSelectedSemesterNum] = useState(() => {
    const val = sessionStorage.getItem('semesters_num');
    return val ? parseInt(val, 10) : undefined;
  });
  const [currentPage, setCurrentPage] = useState(() => {
    const val = sessionStorage.getItem('semesters_page');
    return val ? parseInt(val, 10) : 1;
  });
  const [pageSize, setPageSize] = useState(10);

  // Form Modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [editingSemester, setEditingSemester] = useState(null);
  const [semesterForm] = Form.useForm();
  const watchTrackId = Form.useWatch('academic_track_id', semesterForm);

  // Deletion modal state
  const [depModalOpen, setDepModalOpen] = useState(false);
  const [semesterToDelete, setSemesterToDelete] = useState(null);
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

  // 1. Fetch all academic tracks for dropdowns and mapping
  const { data: trackListData } = useQuery({
    queryKey: ['allTracksList'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/admin/tracks?limit=200');
      return response.data;
    },
  });

  // 2. Fetch semesters
  const {
    data: semesterListData,
    isLoading: isSemesterLoading,
    refetch: refetchSemesters,
  } = useQuery({
    queryKey: ['adminSemestersGlobal', currentPage, pageSize, searchText, selectedTrackId, selectedSemesterNum],
    queryFn: async () => {
      const skip = (currentPage - 1) * pageSize;
      const params = { skip, limit: pageSize };
      if (searchText) params.search = searchText;
      if (selectedTrackId) params.academic_track_id = selectedTrackId;
      if (selectedSemesterNum) params.semester_number = selectedSemesterNum;

      const response = await apiClient.get('/api/v1/admin/semesters', { params });
      return response.data;
    },
  });

  // 3. CRUD Mutations
  const createSemesterMutation = useMutation({
    mutationFn: async (values) => {
      const response = await apiClient.post('/api/v1/admin/semesters', values);
      return response.data;
    },
    onSuccess: () => {
      message.success('Semester created successfully.');
      setIsFormDirty(false);
      setModalOpen(false);
      semesterForm.resetFields();
      queryClient.invalidateQueries({ queryKey: ['adminSemestersGlobal'] });
      queryClient.invalidateQueries({ queryKey: ['adminTracksGlobal'] });
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || 'Failed to create semester.');
    },
  });

  const updateSemesterMutation = useMutation({
    mutationFn: async ({ id, values }) => {
      const response = await apiClient.put(`/api/v1/admin/semesters/${id}`, values);
      return response.data;
    },
    onSuccess: () => {
      message.success('Semester updated successfully.');
      setIsFormDirty(false);
      setModalOpen(false);
      setEditingSemester(null);
      semesterForm.resetFields();
      queryClient.invalidateQueries({ queryKey: ['adminSemestersGlobal'] });
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || 'Failed to update semester.');
    },
  });

  const deleteSemesterMutation = useMutation({
    mutationFn: async (id) => {
      const response = await apiClient.delete(`/api/v1/admin/semesters/${id}`);
      return response.data;
    },
    onSuccess: () => {
      message.success('Semester soft-deleted successfully.');
      setDepModalOpen(false);
      setSemesterToDelete(null);
      setDepCounts(null);
      queryClient.invalidateQueries({ queryKey: ['adminSemestersGlobal'] });
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || 'Failed to delete semester.');
    },
  });

  // Map tracks list to index map for easy lookup
  const trackMap = {};
  trackListData?.tracks?.forEach((t) => {
    trackMap[t.id] = t;
  });

  // Custom Form validator for semester_number based on academic track degree level
  const validateSemesterNumber = (_, value) => {
    if (value === undefined || value === null || value === '') {
      return Promise.reject(new Error('Please input the semester number'));
    }
    const num = parseInt(value, 10);
    if (isNaN(num) || num < 1 || num > 10) {
      return Promise.reject(new Error('Semester number must be an integer between 1 and 10'));
    }

    if (watchTrackId) {
      const selectedTrack = trackMap[watchTrackId];
      if (selectedTrack) {
        const level = selectedTrack.level;
        if (level === 'bachelor' && num > 6) {
          return Promise.reject(new Error('Bachelor tracks only support semesters S1 to S6.'));
        }
        if (level === 'master' && num > 4) {
          return Promise.reject(new Error('Master tracks only support semesters S1 to S4.'));
        }
      }
    }
    return Promise.resolve();
  };

  const handleFormSubmit = (values) => {
    const payload = {
      ...values,
      semester_number: parseInt(values.semester_number, 10),
      ects_required: values.ects_required ? parseInt(values.ects_required, 10) : 0,
    };
    if (editingSemester) {
      updateSemesterMutation.mutate({ id: editingSemester.id, values: payload });
    } else {
      createSemesterMutation.mutate(payload);
    }
  };

  const showCreateModal = () => {
    setEditingSemester(null);
    setIsFormDirty(false);
    semesterForm.resetFields();
    semesterForm.setFieldsValue({ ects_required: 30 }); // typical default
    setModalOpen(true);
  };

  const showEditModal = (record) => {
    setEditingSemester(record);
    setIsFormDirty(false);
    semesterForm.setFieldsValue({
      academic_track_id: record.academic_track_id,
      name: record.name,
      name_de: record.name_de,
      semester_number: record.semester_number,
      ects_required: record.ects_required,
      description: record.description,
      description_de: record.description_de,
    });
    setModalOpen(true);
  };

  const handleCancelSemesterModal = () => {
    if (isFormDirty) {
      Modal.confirm({
        title: 'Discard unsaved changes?',
        content: 'You have unsaved semester profile changes. Are you sure you want to discard them?',
        okText: 'Yes, Discard',
        cancelText: 'No, Keep Editing',
        onOk: () => {
          setModalOpen(false);
          setIsFormDirty(false);
          semesterForm.resetFields();
        },
      });
    } else {
      setModalOpen(false);
      semesterForm.resetFields();
    }
  };

  const showDeleteWarning = async (record) => {
    setSemesterToDelete(record);
    setIsDepLoading(true);
    setDepModalOpen(true);
    try {
      const response = await apiClient.get(`/api/v1/admin/semesters/${record.id}/dependents`);
      setDepCounts(response.data);
    } catch (err) {
      message.error('Failed to query dependent counts.');
      setDepModalOpen(false);
    } finally {
      setIsDepLoading(false);
    }
  };

  const handleConfirmDelete = () => {
    if (semesterToDelete) {
      deleteSemesterMutation.mutate(semesterToDelete.id);
    }
  };

  const columns = [
    {
      title: lang === 'de' ? 'Semester' : 'Semester',
      key: 'semester_name',
      width: 140,
      render: (_, record) => {
        const primary = lang === 'de' ? (record.name_de || record.name) : (record.name || record.name_de);
        const secondary = lang === 'de' ? (record.name_de ? record.name : '') : (record.name ? record.name_de : '');
        return (
          <Space direction="vertical" size={0}>
            <Tag color="geekblue" style={{ fontSize: 13, fontWeight: 'bold' }}>
              {primary}
            </Tag>
            {secondary && (
              <Text type="secondary" style={{ fontSize: 11 }}>
                {lang === 'de' ? `EN: ${secondary}` : `DE: ${secondary}`}
              </Text>
            )}
          </Space>
        );
      },
    },
    {
      title: lang === 'de' ? 'Studienrichtung' : 'Academic Track',
      key: 'academic_track',
      render: (_, record) => {
        const track = trackMap[record.academic_track_id];
        if (!track) return '—';
        const trackName = lang === 'de' ? (track.name_de || track.name) : (track.name || track.name_de);
        return (
          <Space direction="vertical" size={0}>
            <Text strong style={{ fontSize: 13 }}>{trackName}</Text>
            <Tag color={track.level === 'master' ? 'cyan' : track.level === 'bachelor' ? 'blue' : 'gold'} style={{ fontSize: 10, margin: 0 }}>
              {track.level.toUpperCase()}
            </Tag>
          </Space>
        );
      },
    },
    {
      title: 'Semester #',
      dataIndex: 'semester_number',
      key: 'semester_number',
      width: 110,
      render: (num) => <Text>S{num}</Text>,
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
          <Tooltip title="Edit Semester Details">
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
            <Tooltip title="Delete Semester">
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
            <Breadcrumb.Item>Semesters</Breadcrumb.Item>
          </Breadcrumb>
          <Title level={2} style={{ margin: 0 }}>Semester Configuration</Title>
          <Paragraph style={{ margin: 0, marginTop: 4 }}>
            Define semester-level structures, ECTS goals, and assign them to academic tracks.
          </Paragraph>
        </div>

        {isSuperAdmin && (
          <Button type="primary" icon={<PlusOutlined />} onClick={showCreateModal}>
            Add Semester
          </Button>
        )}
      </div>

      {/* Filter and Search Panel */}
      <Card style={{ marginBottom: 24, boxShadow: '0 1px 2px rgba(0,0,0,0.03)' }} bodyStyle={{ padding: '16px 24px' }}>
        <Row gutter={16} align="middle">
          <Col xs={24} md={8}>
            <Input
              placeholder="Search semesters..."
              prefix={<SearchOutlined style={{ color: '#bfbfbf' }} />}
              value={searchText}
              onChange={(e) => {
                const val = e.target.value;
                setSearchText(val);
                sessionStorage.setItem('semesters_search', val);
                setCurrentPage(1);
                sessionStorage.setItem('semesters_page', '1');
              }}
              allowClear
            />
          </Col>
          <Col xs={24} md={8}>
            <Select
              style={{ width: '100%' }}
              placeholder="Filter by Academic Track"
              value={selectedTrackId}
              onChange={(val) => {
                setSelectedTrackId(val || undefined);
                if (val) {
                  sessionStorage.setItem('semesters_track_id', val);
                } else {
                  sessionStorage.removeItem('semesters_track_id');
                }
                setCurrentPage(1);
                sessionStorage.setItem('semesters_page', '1');
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
          <Col xs={24} md={4}>
            <Select
              style={{ width: '100%' }}
              placeholder="Semester #"
              value={selectedSemesterNum}
              onChange={(val) => {
                setSelectedSemesterNum(val || undefined);
                if (val) {
                  sessionStorage.setItem('semesters_num', String(val));
                } else {
                  sessionStorage.removeItem('semesters_num');
                }
                setCurrentPage(1);
                sessionStorage.setItem('semesters_page', '1');
              }}
              allowClear
            >
              {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((num) => (
                <Option key={num} value={num}>
                  S{num}
                </Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} md={4} style={{ textAlign: 'right' }}>
            <Button icon={<ReloadOutlined />} onClick={() => refetchSemesters()}>
              Reload
            </Button>
          </Col>
        </Row>
      </Card>

      {/* Main Table */}
      <Table
        scroll={{ x: 'max-content' }}
        columns={columns}
        dataSource={semesterListData?.semesters || []}
        rowKey="id"
        loading={isSemesterLoading}
        pagination={{
          current: currentPage,
          pageSize: pageSize,
          total: semesterListData?.total || 0,
          showSizeChanger: true,
          pageSizeOptions: ['5', '10', '20', '50'],
          onChange: (p, ps) => {
            setCurrentPage(p);
            sessionStorage.setItem('semesters_page', String(p));
            setPageSize(ps);
          },
        }}
        locale={{
          emptyText: 'No semesters found matching criteria.',
        }}
      />

      {/* Add/Edit Modal */}
      <Modal
        title={editingSemester ? 'Edit Semester' : 'Create Semester'}
        open={modalOpen}
        onCancel={handleCancelSemesterModal}
        footer={null}
        destroyOnClose
      >
        <Form
          form={semesterForm}
          layout="vertical"
          onFinish={handleFormSubmit}
          onValuesChange={() => setIsFormDirty(true)}
          style={{ marginTop: 16 }}
        >
          <Form.Item
            name="academic_track_id"
            label="Belongs to Academic Track"
            rules={[{ required: true, message: 'Please select an academic track' }]}
          >
            <Select placeholder="Select track...">
              {trackListData?.tracks?.map((track) => (
                <Option key={track.id} value={track.id}>
                  {track.name} ({track.level})
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Row gutter={16}>
            <Col span={14}>
              <Form.Item
                name="name"
                label="Semester Name (English)"
                rules={[
                  { required: true, message: 'Please input the semester name' },
                  { max: 100, message: 'Must be 100 characters or less' },
                  germanTextRule,
                ]}
              >
                <Input placeholder="e.g. S1" />
              </Form.Item>
            </Col>
            <Col span={10}>
              <Form.Item
                name="semester_number"
                label="Semester Number"
                rules={[{ validator: validateSemesterNumber }]}
              >
                <Input type="number" min={1} max={10} placeholder="e.g. 1" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="name_de"
            label="Semester Name (German)"
            rules={[
              { max: 100, message: 'Must be 100 characters or less' },
              germanTextRule,
            ]}
          >
            <Input placeholder="e.g. 1. Semester" />
          </Form.Item>

          <Form.Item
            name="ects_required"
            label="ECTS Required for this Semester"
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
            <Input type="number" min={0} placeholder="e.g. 30" />
          </Form.Item>

          <Form.Item
            name="description"
            label="English Description"
            rules={[germanTextRule]}
          >
            <Input.TextArea rows={3} placeholder="Provide details about semester objectives..." />
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
              <Button onClick={handleCancelSemesterModal}>Cancel</Button>
              <Button
                type="primary"
                htmlType="submit"
                loading={createSemesterMutation.isPending || updateSemesterMutation.isPending}
              >
                {editingSemester ? 'Save Changes' : 'Create Semester'}
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
        okText="Yes, Soft-Delete Semester"
        okButtonProps={{
          danger: true,
          loading: deleteSemesterMutation.isPending,
          disabled: depCounts && depCounts.courses_count > 0, // Block deletion if courses exist
        }}
        confirmLoading={deleteSemesterMutation.isPending}
        destroyOnClose
      >
        <div style={{ marginTop: 16 }}>
          <Paragraph>
            Are you sure you want to delete semester <Text strong>{semesterToDelete?.name}</Text>?
          </Paragraph>
          <Paragraph type="secondary">
            This action performs a soft deletion. It will mark the semester and its associated teaching units as deleted.
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
                  <li>Teaching units to delete: <Text strong>{depCounts.teaching_units_count ?? 0}</Text></li>
                  <li>Courses linked: <Text strong>{depCounts.courses_count ?? 0}</Text></li>
                </ul>

                {depCounts.courses_count > 0 && (
                  <div style={{ marginTop: 12, color: '#d4380d', fontWeight: 'bold' }}>
                    <WarningOutlined /> Deletion is BLOCKED because there are active courses assigned to this semester. You must delete or re-assign the courses first.
                  </div>
                )}
              </Card>
            )}
          </Spin>
        </div>
      </Modal>

      {/* History Drawer */}
      <Drawer
        title="Semester Change History"
        placement="right"
        width={480}
        onClose={() => {
          setHistoryDrawerOpen(false);
          setHistoryEntityId(null);
        }}
        open={historyDrawerOpen}
        destroyOnClose
      >
        <EntityHistory entityType="semester" entityId={historyEntityId} />
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

export default Semesters;
