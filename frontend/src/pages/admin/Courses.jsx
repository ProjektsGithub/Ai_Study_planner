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
  Spin,
  Card,
  Typography,
  Breadcrumb,
  Modal,
  Form,
  Row,
  Col,
  Select,
  Tag,
  Slider,
  Rate,
  Drawer,
  Alert,
  Tooltip,
  Divider,
  Popconfirm,
  List,
  InputNumber,
  message,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SearchOutlined,
  ReloadOutlined,
  LinkOutlined,
  PartitionOutlined,
  CheckOutlined,
  CloseOutlined,
  WarningOutlined,
  FolderOpenOutlined,
  HistoryOutlined,
} from '@ant-design/icons';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';

const { Title, Paragraph, Text } = Typography;
const { Option } = Select;

const Courses = () => {
  const queryClient = useQueryClient();
  const { hasRole } = useAuth();
  const isSuperAdmin = hasRole('super_admin');
  const isCoordinator = hasRole('program_coordinator');
  const canEdit = isSuperAdmin || isCoordinator;
  const { lang } = useLanguage();

  // Search & Filter state
  const [searchText, setSearchText] = useState(() => sessionStorage.getItem('courses_search') || '');
  const [selectedProgramId, setSelectedProgramId] = useState(() => sessionStorage.getItem('courses_program_id') || undefined);
  const [selectedSemesterId, setSelectedSemesterId] = useState(() => sessionStorage.getItem('courses_semester_id') || undefined);
  const [selectedUnitId, setSelectedUnitId] = useState(() => sessionStorage.getItem('courses_unit_id') || undefined);
  const [ectsRange, setEctsRange] = useState(() => {
    const val = sessionStorage.getItem('courses_ects_range');
    return val ? JSON.parse(val) : [1, 30];
  });
  const [selectedDifficulty, setSelectedDifficulty] = useState(() => {
    const val = sessionStorage.getItem('courses_difficulty');
    return val ? parseInt(val, 10) : undefined;
  });
  const [currentPage, setCurrentPage] = useState(() => {
    const val = sessionStorage.getItem('courses_page');
    return val ? parseInt(val, 10) : 1;
  });
  const [pageSize, setPageSize] = useState(10);

  // Table row selection & Inline editing states
  const [selectedRowKeys, setSelectedRowKeys] = useState([]);
  const [editingRowKey, setEditingRowKey] = useState('');
  const [inlineForm] = Form.useForm();

  // Course Form Modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [editingCourse, setEditingCourse] = useState(null);
  const [courseForm] = Form.useForm();
  const watchSemesterId = Form.useWatch('semester_id', courseForm);

  // Prerequisite Drawer state
  const [prereqDrawerOpen, setPrereqDrawerOpen] = useState(false);
  const [activeCourse, setActiveCourse] = useState(null);
  const [selectedNewPrereqId, setSelectedNewPrereqId] = useState(undefined);
  const [cycleError, setCycleError] = useState(null);
  const [isValidating, setIsValidating] = useState(false);

  // Prerequisite Chain Drawer state
  const [chainDrawerOpen, setChainDrawerOpen] = useState(false);

  // History Drawer states
  const [historyDrawerOpen, setHistoryDrawerOpen] = useState(false);
  const [historyEntityId, setHistoryEntityId] = useState(null);

  // Batch edit modals
  const [batchEctsModalOpen, setBatchEctsModalOpen] = useState(false);
  const [batchDifficultyModalOpen, setBatchDifficultyModalOpen] = useState(false);
  const [batchEctsValue, setBatchEctsValue] = useState(6);
  const [batchDifficultyValue, setBatchDifficultyValue] = useState(3);

  // Dirty form state
  const [isFormDirty, setIsFormDirty] = useState(false);

  const blocker = useBlocker(
    ({ currentValue, nextLocation }) =>
      (isFormDirty || !!editingRowKey) && currentValue.pathname !== nextLocation.pathname
  );

  const germanTextRule = {
    pattern: /^[a-zA-ZäöüßÄÖÜ0-9\s\.,\-\(\)\/\':;&\!?%@#\+\*\[\]]*$/,
    message: 'Invalid characters. German letters (ä, ö, ü, ß) and common punctuation are supported.',
  };

  // 1. Fetch programs
  const { data: programListData } = useQuery({
    queryKey: ['allProgramsList'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/admin/programs?limit=200');
      return response.data;
    },
  });

  // 2. Fetch tracks
  const { data: trackListData } = useQuery({
    queryKey: ['allTracksList'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/admin/tracks?limit=200');
      return response.data;
    },
  });

  // 3. Fetch semesters
  const { data: semesterListData } = useQuery({
    queryKey: ['allSemestersList'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/admin/semesters?limit=1000');
      return response.data;
    },
  });

  // 4. Fetch teaching units
  const { data: unitListData } = useQuery({
    queryKey: ['allUnitsList'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/admin/teaching-units?limit=1000');
      return response.data;
    },
  });

  // 5. Fetch courses (paginated, filtered)
  const {
    data: courseListData,
    isLoading: isCoursesLoading,
    refetch: refetchCourses,
  } = useQuery({
    queryKey: [
      'adminCoursesGlobal',
      currentPage,
      pageSize,
      searchText,
      selectedProgramId,
      selectedSemesterId,
      selectedUnitId,
      ectsRange,
      selectedDifficulty,
    ],
    queryFn: async () => {
      const skip = (currentPage - 1) * pageSize;
      const params = {
        skip,
        limit: pageSize,
        ects_min: ectsRange[0],
        ects_max: ectsRange[1],
      };
      if (searchText) params.search = searchText;
      if (selectedProgramId) params.program_id = selectedProgramId;
      if (selectedSemesterId) params.semester_id = selectedSemesterId;
      if (selectedUnitId) params.teaching_unit_id = selectedUnitId;
      if (selectedDifficulty) params.difficulty = selectedDifficulty;

      const response = await apiClient.get('/api/v1/admin/courses', { params });
      return response.data;
    },
  });

  // 6. Fetch prerequisites for the active course
  const { data: activeCoursePrereqs, refetch: refetchActivePrereqs } = useQuery({
    queryKey: ['activeCoursePrereqs', activeCourse?.id],
    queryFn: async () => {
      if (!activeCourse) return null;
      const response = await apiClient.get(`/api/v1/admin/courses/${activeCourse.id}/prerequisites`);
      return response.data;
    },
    enabled: !!activeCourse,
  });

  // 7. Fetch dependents for the active course
  const { data: activeCourseDependents } = useQuery({
    queryKey: ['activeCourseDependents', activeCourse?.id],
    queryFn: async () => {
      if (!activeCourse) return null;
      const response = await apiClient.get(`/api/v1/admin/courses/${activeCourse.id}/dependents`);
      return response.data;
    },
    enabled: !!activeCourse,
  });

  // 8. Fetch complete prerequisite chain (BFS traversal)
  const { data: activePrereqChain, isLoading: isChainLoading } = useQuery({
    queryKey: ['activePrereqChain', activeCourse?.id],
    queryFn: async () => {
      if (!activeCourse) return null;
      const response = await apiClient.get(`/api/v1/admin/prerequisites/chain/${activeCourse.id}`);
      return response.data;
    },
    enabled: !!activeCourse && chainDrawerOpen,
  });

  // Fetch all potential prerequisite courses (same study program)
  const activeCourseProgramId = activeCourse
    ? semesterListData?.semesters?.find((s) => s.id === activeCourse.semester_id)
        ? trackListData?.tracks?.find(
            (t) => t.id === semesterListData.semesters.find((s) => s.id === activeCourse.semester_id).academic_track_id
          )?.study_program_id
        : null
    : null;

  const { data: programCoursesData } = useQuery({
    queryKey: ['programCoursesList', activeCourseProgramId],
    queryFn: async () => {
      if (!activeCourseProgramId) return null;
      const response = await apiClient.get('/api/v1/admin/courses', {
        params: { program_id: activeCourseProgramId, limit: 500 },
      });
      return response.data;
    },
    enabled: !!activeCourseProgramId,
  });

  // Maps
  const programMap = {};
  programListData?.programs?.forEach((p) => {
    programMap[p.id] = p;
  });

  const trackMap = {};
  trackListData?.tracks?.forEach((t) => {
    trackMap[t.id] = t;
  });

  const semesterMap = {};
  semesterListData?.semesters?.forEach((s) => {
    semesterMap[s.id] = s;
  });

  const unitMap = {};
  unitListData?.teaching_units?.forEach((u) => {
    unitMap[u.id] = u;
  });

  // Mutators
  const createCourseMutation = useMutation({
    mutationFn: async (values) => {
      const response = await apiClient.post('/api/v1/admin/courses', values);
      return response.data;
    },
    onSuccess: () => {
      message.success('Course created successfully.');
      setIsFormDirty(false);
      setModalOpen(false);
      courseForm.resetFields();
      queryClient.invalidateQueries({ queryKey: ['adminCoursesGlobal'] });
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || 'Failed to create course.');
    },
  });

  const updateCourseMutation = useMutation({
    mutationFn: async ({ id, values }) => {
      const response = await apiClient.put(`/api/v1/admin/courses/${id}`, values);
      return response.data;
    },
    onSuccess: () => {
      message.success('Course updated successfully.');
      setIsFormDirty(false);
      setModalOpen(false);
      setEditingCourse(null);
      setEditingRowKey('');
      courseForm.resetFields();
      queryClient.invalidateQueries({ queryKey: ['adminCoursesGlobal'] });
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || 'Failed to update course.');
    },
  });

  const deleteCourseMutation = useMutation({
    mutationFn: async (id) => {
      const response = await apiClient.delete(`/api/v1/admin/courses/${id}`);
      return response.data;
    },
    onSuccess: () => {
      message.success('Course soft-deleted successfully.');
      queryClient.invalidateQueries({ queryKey: ['adminCoursesGlobal'] });
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || 'Failed to delete course.');
    },
  });

  // Batch actions mutations
  const batchOperationMutation = useMutation({
    mutationFn: async (payload) => {
      const response = await apiClient.post('/api/v1/admin/courses/batch', payload);
      return response.data;
    },
    onSuccess: (data) => {
      if (data.error_count > 0) {
        message.warning(`Batch operation completed with ${data.error_count} errors.`);
        Modal.error({
          title: 'Batch Operation Failures',
          content: (
            <div style={{ maxHeight: 300, overflowY: 'auto' }}>
              {data.errors.map((err, i) => (
                <div key={i} style={{ marginBottom: 8 }}>
                  <Text type="danger">ID {err.id}:</Text> {err.detail}
                </div>
              ))}
            </div>
          ),
        });
      } else {
        message.success('Batch operation completed successfully.');
      }
      setSelectedRowKeys([]);
      setBatchEctsModalOpen(false);
      setBatchDifficultyModalOpen(false);
      queryClient.invalidateQueries({ queryKey: ['adminCoursesGlobal'] });
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || 'Failed to execute batch operation.');
    },
  });

  // Prerequisite Linking Mutations
  const addPrereqMutation = useMutation({
    mutationFn: async (payload) => {
      const response = await apiClient.post('/api/v1/admin/prerequisites', payload);
      return response.data;
    },
    onSuccess: () => {
      message.success('Prerequisite linked successfully.');
      setSelectedNewPrereqId(undefined);
      refetchActivePrereqs();
      queryClient.invalidateQueries({ queryKey: ['adminCoursesGlobal'] });
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || 'Failed to link prerequisite.');
    },
  });

  // Inline row edits
  const isEditingInline = (record) => record.id === editingRowKey;

  const startInlineEdit = (record) => {
    inlineForm.setFieldsValue({
      name: record.name,
      ects_credits: record.ects_credits,
      coefficient: record.coefficient,
      difficulty_level: record.difficulty_level,
    });
    setEditingRowKey(record.id);
  };

  const cancelInlineEdit = () => {
    setEditingRowKey('');
  };

  const saveInlineEdit = async (id) => {
    try {
      const row = await inlineForm.validateFields();
      updateCourseMutation.mutate({ id, values: row });
    } catch (errInfo) {
      message.error('Validation failed: check course details.');
    }
  };

  // Submit standard course form
  const handleCourseSubmit = (values) => {
    const payload = {
      ...values,
      ects_credits: parseInt(values.ects_credits, 10),
      coefficient: parseFloat(values.coefficient),
      difficulty_level: parseInt(values.difficulty_level, 10),
    };
    if (editingCourse) {
      updateCourseMutation.mutate({ id: editingCourse.id, values: payload });
    } else {
      createCourseMutation.mutate(payload);
    }
  };

  const showCreateModal = () => {
    setEditingCourse(null);
    setIsFormDirty(false);
    courseForm.resetFields();
    courseForm.setFieldsValue({ ects_credits: 6, coefficient: 1.0, difficulty_level: 3 });
    setModalOpen(true);
  };

  const showEditModal = (record) => {
    setEditingCourse(record);
    setIsFormDirty(false);
    courseForm.setFieldsValue({
      semester_id: record.semester_id,
      teaching_unit_id: record.teaching_unit_id || undefined,
      name: record.name,
      name_de: record.name_de,
      code: record.code,
      ects_credits: record.ects_credits,
      coefficient: record.coefficient,
      difficulty_level: record.difficulty_level,
      description: record.description,
      description_de: record.description_de,
    });
    setModalOpen(true);
  };

  const handleCancelCourseModal = () => {
    if (isFormDirty) {
      Modal.confirm({
        title: 'Discard unsaved changes?',
        content: 'You have unsaved course profile changes. Are you sure you want to discard them?',
        okText: 'Yes, Discard',
        cancelText: 'No, Keep Editing',
        onOk: () => {
          setModalOpen(false);
          setIsFormDirty(false);
          courseForm.resetFields();
        },
      });
    } else {
      setModalOpen(false);
      courseForm.resetFields();
    }
  };

  // Handle Prerequisite Drawer open
  const openPrereqDrawer = (record) => {
    setActiveCourse(record);
    setSelectedNewPrereqId(undefined);
    setCycleError(null);
    setPrereqDrawerOpen(true);
  };

  // Pre-flight link validation & Link saving
  const handleAddPrerequisite = async () => {
    if (!selectedNewPrereqId || !activeCourse) return;
    setIsValidating(true);
    setCycleError(null);
    try {
      // 1. Pre-flight check
      const response = await apiClient.post('/api/v1/admin/prerequisites/validate', {
        course_id: activeCourse.id,
        prerequisite_id: selectedNewPrereqId,
      });

      if (!response.data.is_valid) {
        setCycleError(response.data.error_message || 'Circular dependency detected.');
      } else {
        // 2. Perform the actual post if valid
        addPrereqMutation.mutate({
          course_id: activeCourse.id,
          prerequisite_id: selectedNewPrereqId,
        });
      }
    } catch (err) {
      message.error('Failed to validate prerequisite relationship.');
    } finally {
      setIsValidating(false);
    }
  };

  // Unlinking a prerequisite
  const handleRemovePrerequisite = async (prereqId) => {
    if (!activeCourse) return;
    try {
      // Find the relationship record ID
      const response = await apiClient.get('/api/v1/admin/prerequisites', {
        params: { course_id: activeCourse.id, prerequisite_id: prereqId },
      });
      const relationship = response.data.prerequisites?.[0];
      if (relationship) {
        // Delete by row ID
        await apiClient.delete(`/api/v1/admin/prerequisites/${relationship.id}`);
        message.success('Prerequisite removed.');
        refetchActivePrereqs();
        queryClient.invalidateQueries({ queryKey: ['adminCoursesGlobal'] });
      } else {
        message.error('Relationship record not found.');
      }
    } catch (err) {
      message.error('Failed to remove prerequisite relationship.');
    }
  };

  // Batch delete confirmation
  const handleBatchDelete = () => {
    Modal.confirm({
      title: 'Confirm Batch Delete',
      icon: <WarningOutlined style={{ color: '#f5222d' }} />,
      content: `Are you sure you want to soft-delete the ${selectedRowKeys.length} selected courses?`,
      okText: 'Yes, Delete All',
      okButtonProps: { danger: true },
      onOk: () => {
        batchOperationMutation.mutate({
          operation: 'delete',
          delete_ids: selectedRowKeys,
        });
      },
    });
  };

  // Batch Update ECTS handler
  const handleBatchUpdateEcts = () => {
    batchOperationMutation.mutate({
      operation: 'update',
      update_items: selectedRowKeys.map((id) => ({
        id,
        ects_credits: batchEctsValue,
      })),
    });
  };

  // Batch Update Difficulty handler
  const handleBatchUpdateDifficulty = () => {
    batchOperationMutation.mutate({
      operation: 'update',
      update_items: selectedRowKeys.map((id) => ({
        id,
        difficulty_level: batchDifficultyValue,
      })),
    });
  };

  const columns = [
    {
      title: 'Code',
      dataIndex: 'code',
      key: 'code',
      width: 110,
      render: (code) => code ? <Tag color="blue">{code}</Tag> : '—',
    },
    {
      title: 'Course Name',
      key: 'name',
      render: (_, record) => {
        if (isEditingInline(record)) {
          return (
            <Form.Item
              name="name"
              form={inlineForm}
              style={{ margin: 0 }}
              rules={[
                { required: true, message: 'Required' },
                germanTextRule,
              ]}
            >
              <Input size="small" />
            </Form.Item>
          );
        }
        return (
          <Space direction="vertical" size={0}>
            <Text strong style={{ fontSize: 13 }}>
              {lang === 'de' ? (record.name_de || record.name) : (record.name || record.name_de)}
            </Text>
            {lang === 'de' && record.name_de && record.name && (
              <Text type="secondary" style={{ fontSize: 11 }}>
                EN: {record.name}
              </Text>
            )}
            {lang === 'en' && record.name_de && record.name && (
              <Text type="secondary" style={{ fontSize: 11 }}>
                DE: {record.name_de}
              </Text>
            )}
          </Space>
        );
      },
    },
    {
      title: 'Semester / Track',
      key: 'semester',
      width: 170,
      render: (_, record) => {
        const sem = semesterMap[record.semester_id];
        const track = sem ? trackMap[sem.academic_track_id] : null;
        if (!sem) return '—';
        const semName = lang === 'de' ? (sem.name_de || sem.name) : (sem.name || sem.name_de);
        const trackName = track ? (lang === 'de' ? (track.name_de || track.name) : (track.name || track.name_de)) : '';
        return (
          <Space direction="vertical" size={0}>
            <Text style={{ fontSize: 12 }}>{semName} (S{sem.semester_number})</Text>
            {trackName && (
              <Tag color="cyan" style={{ fontSize: 9, margin: 0 }}>
                {trackName}
              </Tag>
            )}
          </Space>
        );
      },
    },
    {
      title: 'ECTS',
      dataIndex: 'ects_credits',
      key: 'ects_credits',
      width: 90,
      render: (ects, record) => {
        if (isEditingInline(record)) {
          return (
            <Form.Item
              name="ects_credits"
              form={inlineForm}
              style={{ margin: 0 }}
              rules={[
                { required: true, message: '1-30' },
                {
                  validator: (_, value) => {
                    if (value !== undefined && value !== null && (isNaN(value) || parseInt(value, 10) < 1 || parseInt(value, 10) > 30)) {
                      return Promise.reject(new Error('Must be 1-30'));
                    }
                    return Promise.resolve();
                  },
                },
              ]}
            >
              <InputNumber size="small" min={1} max={30} style={{ width: '100%' }} />
            </Form.Item>
          );
        }
        return <Text strong>{ects} Cr</Text>;
      },
    },
    {
      title: 'Coeff.',
      dataIndex: 'coefficient',
      key: 'coefficient',
      width: 90,
      render: (coeff, record) => {
        if (isEditingInline(record)) {
          return (
            <Form.Item
              name="coefficient"
              form={inlineForm}
              style={{ margin: 0 }}
              rules={[
                { required: true, message: '0.1-10' },
                {
                  validator: (_, value) => {
                    if (value !== undefined && value !== null && (isNaN(value) || parseFloat(value) < 0.1 || parseFloat(value) > 10.0)) {
                      return Promise.reject(new Error('Must be 0.1-10'));
                    }
                    return Promise.resolve();
                  },
                },
              ]}
            >
              <InputNumber size="small" min={0.1} max={10} step={0.1} style={{ width: '100%' }} />
            </Form.Item>
          );
        }
        return <Text>{coeff}</Text>;
      },
    },
    {
      title: 'Difficulty',
      dataIndex: 'difficulty_level',
      key: 'difficulty_level',
      width: 110,
      render: (diff, record) => {
        if (isEditingInline(record)) {
          return (
            <Form.Item
              name="difficulty_level"
              form={inlineForm}
              style={{ margin: 0 }}
            >
              <Select size="small" style={{ width: '100%' }}>
                {[1, 2, 3, 4, 5].map((n) => (
                  <Option key={n} value={n}>
                    {n}
                  </Option>
                ))}
              </Select>
            </Form.Item>
          );
        }
        return <Rate disabled defaultValue={diff} count={5} style={{ fontSize: 10 }} />;
      },
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 180,
      render: (_, record) => {
        const editable = isEditingInline(record);
        if (editable) {
          return (
            <Space size={8}>
              <Button
                type="text"
                size="small"
                icon={<CheckOutlined style={{ color: '#52c41a' }} />}
                onClick={() => saveInlineEdit(record.id)}
              />
              <Button
                type="text"
                size="small"
                icon={<CloseOutlined style={{ color: '#f5222d' }} />}
                onClick={cancelInlineEdit}
              />
            </Space>
          );
        }

        return (
          <Space size={4}>
            <Tooltip title="Edit Course">
              <Button
                type="text"
                icon={<EditOutlined style={{ color: '#1890ff' }} />}
                onClick={() => showEditModal(record)}
              />
            </Tooltip>
            <Tooltip title="Inline Edit">
              <Button
                type="text"
                icon={<FolderOpenOutlined style={{ color: '#fa8c16' }} />}
                onClick={() => startInlineEdit(record)}
              />
            </Tooltip>
            <Tooltip title="Prerequisites">
              <Button
                type="text"
                icon={<LinkOutlined style={{ color: '#722ed1' }} />}
                onClick={() => openPrereqDrawer(record)}
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
              <Popconfirm
                title="Soft-delete course?"
                onConfirm={() => deleteCourseMutation.mutate(record.id)}
                okText="Yes"
                cancelText="No"
              >
                <Button
                  type="text"
                  icon={<DeleteOutlined style={{ color: '#f5222d' }} />}
                />
              </Popconfirm>
            )}
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
            <Breadcrumb.Item>Courses</Breadcrumb.Item>
          </Breadcrumb>
          <Title level={2} style={{ margin: 0 }}>Course Configuration</Title>
          <Paragraph style={{ margin: 0, marginTop: 4 }}>
            Configure individual course modules, grades weight coefficient, difficulty, and prerequisite links.
          </Paragraph>
        </div>

        {canEdit && (
          <Button type="primary" icon={<PlusOutlined />} onClick={showCreateModal}>
            Add Course
          </Button>
        )}
      </div>

      {/* Advanced Filtering Card */}
      <Card style={{ marginBottom: 24, boxShadow: '0 1px 2px rgba(0,0,0,0.03)' }} bodyStyle={{ padding: '20px 24px' }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={6}>
            <Input
              placeholder="Search by code or name..."
              prefix={<SearchOutlined style={{ color: '#bfbfbf' }} />}
              value={searchText}
              onChange={(e) => {
                const val = e.target.value;
                setSearchText(val);
                sessionStorage.setItem('courses_search', val);
                setCurrentPage(1);
                sessionStorage.setItem('courses_page', '1');
              }}
              allowClear
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Select
              style={{ width: '100%' }}
              placeholder="Filter by Program"
              value={selectedProgramId}
              onChange={(val) => {
                setSelectedProgramId(val || undefined);
                if (val) {
                  sessionStorage.setItem('courses_program_id', val);
                } else {
                  sessionStorage.removeItem('courses_program_id');
                }
                setSelectedSemesterId(undefined);
                setSelectedUnitId(undefined);
                sessionStorage.removeItem('courses_semester_id');
                sessionStorage.removeItem('courses_unit_id');
                setCurrentPage(1);
                sessionStorage.setItem('courses_page', '1');
              }}
              allowClear
            >
              {programListData?.programs?.map((prog) => (
                <Option key={prog.id} value={prog.id}>
                  {prog.name} ({prog.code})
                </Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Select
              style={{ width: '100%' }}
              placeholder="Filter by Semester"
              value={selectedSemesterId}
              onChange={(val) => {
                setSelectedSemesterId(val || undefined);
                if (val) {
                  sessionStorage.setItem('courses_semester_id', val);
                } else {
                  sessionStorage.removeItem('courses_semester_id');
                }
                setSelectedUnitId(undefined);
                sessionStorage.removeItem('courses_unit_id');
                setCurrentPage(1);
                sessionStorage.setItem('courses_page', '1');
              }}
              allowClear
              disabled={!selectedProgramId}
            >
              {semesterListData?.semesters
                ?.filter((s) => {
                  const track = trackMap[s.academic_track_id];
                  return !selectedProgramId || track?.study_program_id === selectedProgramId;
                })
                ?.map((sem) => {
                  const track = trackMap[sem.academic_track_id];
                  return (
                    <Option key={sem.id} value={sem.id}>
                      {sem.name} (S{sem.semester_number}) — {track?.name}
                    </Option>
                  );
                })}
            </Select>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Select
              style={{ width: '100%' }}
              placeholder="Filter by Teaching Unit"
              value={selectedUnitId}
              onChange={(val) => {
                setSelectedUnitId(val || undefined);
                if (val) {
                  sessionStorage.setItem('courses_unit_id', val);
                } else {
                  sessionStorage.removeItem('courses_unit_id');
                }
                setCurrentPage(1);
                sessionStorage.setItem('courses_page', '1');
              }}
              allowClear
              disabled={!selectedSemesterId}
            >
              {unitListData?.teaching_units
                ?.filter((u) => !selectedSemesterId || u.semester_id === selectedSemesterId)
                ?.map((unit) => (
                  <Option key={unit.id} value={unit.id}>
                    {unit.name} ({unit.code || 'UE'})
                  </Option>
                ))}
            </Select>
          </Col>
        </Row>
        <Row gutter={[16, 16]} style={{ marginTop: 16 }} align="middle">
          <Col xs={24} md={10}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <span style={{ fontSize: 13, color: '#8c8c8c', whiteSpace: 'nowrap' }}>ECTS Range:</span>
              <Slider
                range
                min={1}
                max={30}
                value={ectsRange}
                onChange={(val) => {
                  setEctsRange(val);
                  sessionStorage.setItem('courses_ects_range', JSON.stringify(val));
                  setCurrentPage(1);
                  sessionStorage.setItem('courses_page', '1');
                }}
                style={{ flex: 1 }}
              />
              <span style={{ fontSize: 13, fontWeight: 'bold' }}>{ectsRange[0]} - {ectsRange[1]} Cr</span>
            </div>
          </Col>
          <Col xs={24} md={6}>
            <Select
              style={{ width: '100%' }}
              placeholder="Filter by Difficulty"
              value={selectedDifficulty}
              onChange={(val) => {
                setSelectedDifficulty(val || undefined);
                if (val) {
                  sessionStorage.setItem('courses_difficulty', String(val));
                } else {
                  sessionStorage.removeItem('courses_difficulty');
                }
                setCurrentPage(1);
                sessionStorage.setItem('courses_page', '1');
              }}
              allowClear
            >
              {[1, 2, 3, 4, 5].map((num) => (
                <Option key={num} value={num}>
                  Difficulty: {num}
                </Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} md={8} style={{ textAlign: 'right' }}>
            <Space>
              <Button
                icon={<ReloadOutlined />}
                onClick={() => {
                  setSearchText('');
                  setSelectedProgramId(undefined);
                  setSelectedSemesterId(undefined);
                  setSelectedUnitId(undefined);
                  setEctsRange([1, 30]);
                  setSelectedDifficulty(undefined);
                  setCurrentPage(1);
                  sessionStorage.removeItem('courses_search');
                  sessionStorage.removeItem('courses_program_id');
                  sessionStorage.removeItem('courses_semester_id');
                  sessionStorage.removeItem('courses_unit_id');
                  sessionStorage.removeItem('courses_ects_range');
                  sessionStorage.removeItem('courses_difficulty');
                  sessionStorage.setItem('courses_page', '1');
                  refetchCourses();
                }}
              >
                Reset All
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Batch operations bar */}
      {selectedRowKeys.length > 0 && (
        <Alert
          type="info"
          showIcon
          style={{ marginBottom: 16, display: 'flex', alignItems: 'center' }}
          message={
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%', flexWrap: 'wrap', gap: 12 }}>
              <span>
                Selected <Text strong>{selectedRowKeys.length}</Text> courses.
              </span>
              <Space>
                {canEdit && (
                  <>
                    <Button size="small" type="primary" onClick={() => setBatchEctsModalOpen(true)}>
                      Batch Edit ECTS
                    </Button>
                    <Button size="small" onClick={() => setBatchDifficultyModalOpen(true)}>
                      Batch Edit Difficulty
                    </Button>
                  </>
                )}
                {isSuperAdmin && (
                  <Button size="small" danger icon={<DeleteOutlined />} onClick={handleBatchDelete}>
                    Batch Soft-Delete
                  </Button>
                )}
                <Button size="small" onClick={() => setSelectedRowKeys([])}>Cancel</Button>
              </Space>
            </div>
          }
        />
      )}

      {/* Main Table */}
      <Form form={inlineForm} component={false}>
        <Table
          scroll={{ x: 'max-content' }}
          rowSelection={{
            selectedRowKeys,
            onChange: (keys) => setSelectedRowKeys(keys),
          }}
          columns={columns}
          dataSource={courseListData?.courses || []}
          rowKey="id"
          loading={isCoursesLoading}
          pagination={{
            current: currentPage,
            pageSize: pageSize,
            total: courseListData?.total || 0,
            showSizeChanger: true,
            pageSizeOptions: ['5', '10', '20', '50'],
            onChange: (p, ps) => {
              setCurrentPage(p);
              sessionStorage.setItem('courses_page', String(p));
              setPageSize(ps);
            },
          }}
          locale={{
            emptyText: 'No courses found matching criteria.',
          }}
        />
      </Form>

      {/* Add/Edit Modal */}
      <Modal
        title={editingCourse ? 'Edit Course' : 'Create Course'}
        open={modalOpen}
        onCancel={handleCancelCourseModal}
        footer={null}
        destroyOnClose
        width={650}
      >
        <Form
          form={courseForm}
          layout="vertical"
          onFinish={handleCourseSubmit}
          onValuesChange={() => setIsFormDirty(true)}
          style={{ marginTop: 16 }}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="semester_id"
                label="Semester"
                rules={[{ required: true, message: 'Please select parent semester' }]}
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
            </Col>
            <Col span={12}>
              <Form.Item
                name="teaching_unit_id"
                label="Teaching Unit (Optional)"
              >
                <Select placeholder="Select teaching unit..." allowClear disabled={!watchSemesterId}>
                  {unitListData?.teaching_units
                    ?.filter((u) => u.semester_id === watchSemesterId)
                    ?.map((unit) => (
                      <Option key={unit.id} value={unit.id}>
                        {unit.name} ({unit.code || 'UE'})
                      </Option>
                    ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={16}>
              <Form.Item
                name="name"
                label="Course Name (English)"
                rules={[
                  { required: true, message: 'English name is required' },
                  { max: 255, message: 'Must be 255 characters or less' },
                  germanTextRule,
                ]}
              >
                <Input placeholder="e.g. Advanced Programming" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="code"
                label="Course Code"
                rules={[
                  { required: true, message: 'Course code is required' },
                  { max: 50, message: 'Must be 50 characters or less' },
                  {
                    pattern: /^[A-Z0-9]+$/,
                    message: 'Uppercase letters and numbers only',
                  },
                ]}
              >
                <Input placeholder="e.g. CS202" style={{ textTransform: 'uppercase' }} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="name_de"
            label="Course Name (German)"
            rules={[
              { max: 255, message: 'Must be 255 characters or less' },
              germanTextRule,
            ]}
          >
            <Input placeholder="e.g. Fortgeschrittene Programmierung" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="ects_credits"
                label="ECTS Credits (1-30)"
                rules={[
                  { required: true, message: 'Required' },
                  {
                    validator: (_, value) => {
                      if (value !== undefined && value !== null && (isNaN(value) || parseInt(value, 10) < 1 || parseInt(value, 10) > 30)) {
                        return Promise.reject(new Error('Must be between 1 and 30'));
                      }
                      return Promise.resolve();
                    },
                  },
                ]}
              >
                <Input type="number" min={1} max={30} placeholder="e.g. 6" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="coefficient"
                label="Grade Weight Coeff (0.1-10)"
                rules={[
                  { required: true, message: 'Required' },
                  {
                    validator: (_, value) => {
                      if (value !== undefined && value !== null && (isNaN(value) || parseFloat(value) < 0.1 || parseFloat(value) > 10.0)) {
                        return Promise.reject(new Error('Must be between 0.1 and 10.0'));
                      }
                      return Promise.resolve();
                    },
                  },
                ]}
              >
                <Input type="number" step={0.1} min={0.1} max={10.0} placeholder="e.g. 1.0" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="difficulty_level"
                label="Difficulty Level (1-5)"
                rules={[{ required: true, message: 'Required' }]}
              >
                <Select>
                  {[1, 2, 3, 4, 5].map((n) => (
                    <Option key={n} value={n}>
                      Level {n}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="description"
            label="English Description"
            rules={[germanTextRule]}
          >
            <Input.TextArea rows={3} placeholder="Syllabus topic details..." />
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
              <Button onClick={handleCancelCourseModal}>Cancel</Button>
              <Button
                type="primary"
                htmlType="submit"
                loading={createCourseMutation.isPending || updateCourseMutation.isPending}
              >
                {editingCourse ? 'Save Changes' : 'Create Course'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* Prerequisite & Dependents Management Drawer */}
      <Drawer
        title={
          <Space>
            <LinkOutlined />
            <span>Prerequisite Links for: <Text strong>{activeCourse?.name}</Text></span>
          </Space>
        }
        placement="right"
        width={550}
        onClose={() => setPrereqDrawerOpen(false)}
        open={prereqDrawerOpen}
        destroyOnClose
        extra={
          <Button
            type="primary"
            icon={<PartitionOutlined />}
            onClick={() => setChainDrawerOpen(true)}
          >
            Prerequisite Chain
          </Button>
        }
      >
        {activeCourse && (
          <div>
            {/* Cycle error path rendering */}
            {cycleError && (
              <Alert
                message="Circular Dependency Warning"
                description={
                  <div>
                    <Paragraph>{cycleError}</Paragraph>
                    <Text type="secondary">Adding this prerequisite would violate academic structure.</Text>
                  </div>
                }
                type="error"
                showIcon
                closable
                onClose={() => setCycleError(null)}
                style={{ marginBottom: 16 }}
              />
            )}

            <Title level={5} style={{ marginTop: 0 }}>Add New Prerequisite Course</Title>
            <div style={{ display: 'flex', gap: 12, marginBottom: 24 }}>
              <Select
                showSearch
                style={{ flex: 1 }}
                placeholder="Choose a course from same program..."
                value={selectedNewPrereqId}
                onChange={(val) => {
                  setSelectedNewPrereqId(val);
                  setCycleError(null);
                }}
                filterOption={(input, option) =>
                  (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                }
                options={programCoursesData?.courses
                  ?.filter((c) => c.id !== activeCourse.id && !activeCoursePrereqs?.prerequisites?.find((p) => p.id === c.id))
                  ?.map((c) => ({
                    value: c.id,
                    label: `${c.name} (${c.code || 'No Code'})`,
                  }))}
              />
              <Button
                type="primary"
                loading={isValidating || addPrereqMutation.isPending}
                disabled={!selectedNewPrereqId}
                onClick={handleAddPrerequisite}
              >
                Add Link
              </Button>
            </div>

            <Divider />

            <Title level={5}>Direct Prerequisites Required:</Title>
            <List
              dataSource={activeCoursePrereqs?.prerequisites || []}
              locale={{ emptyText: 'No prerequisites assigned.' }}
              renderItem={(item) => (
                <List.Item
                  actions={[
                    <Popconfirm
                      title="Unlink this prerequisite?"
                      onConfirm={() => handleRemovePrerequisite(item.id)}
                      okText="Unlink"
                      okButtonProps={{ danger: true }}
                    >
                      <Button type="text" danger icon={<CloseOutlined />} />
                    </Popconfirm>,
                  ]}
                >
                  <List.Item.Meta
                    title={
                      <Space>
                        <Text strong>{item.name}</Text>
                        {item.code && <Tag color="blue">{item.code}</Tag>}
                      </Space>
                    }
                    description={`S${semesterMap[item.semester_id]?.semester_number || '—'} — ${item.ects_credits} ECTS`}
                  />
                </List.Item>
              )}
            />

            <Divider />

            <Title level={5}>Course is a Prerequisite For (Dependents):</Title>
            <List
              dataSource={activeCourseDependents?.dependents || []}
              locale={{ emptyText: 'No courses depend on this course.' }}
              renderItem={(item) => (
                <List.Item>
                  <List.Item.Meta
                    title={
                      <Space>
                        <Text strong>{item.name}</Text>
                        {item.code && <Tag color="blue">{item.code}</Tag>}
                      </Space>
                    }
                    description={`S${semesterMap[item.semester_id]?.semester_number || '—'} — ${item.ects_credits} ECTS`}
                  />
                </List.Item>
              )}
            />
          </div>
        )}
      </Drawer>

      {/* BFS Prerequisite Chain Drawer */}
      <Drawer
        title={
          <Space>
            <PartitionOutlined />
            <span>Transitive Prerequisite Chain: <Text strong>{activeCourse?.name}</Text></span>
          </Space>
        }
        placement="right"
        width={450}
        onClose={() => setChainDrawerOpen(false)}
        open={chainDrawerOpen}
        destroyOnClose
      >
        <Spin spinning={isChainLoading}>
          {activePrereqChain && (
            <div>
              <Paragraph>
                This visualizes the complete sequence of courses required to unlock <Text strong>{activeCourse?.name}</Text> based on traversal depth (Level 1 are direct pre-reqs).
              </Paragraph>

              <List
                dataSource={activePrereqChain.chain || []}
                locale={{ emptyText: 'No prerequisites chain found.' }}
                renderItem={(item) => (
                  <Card size="small" style={{ marginBottom: 12, borderLeft: '4px solid #722ed1' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <div>
                        <Text strong style={{ fontSize: 13 }}>{item.course_name}</Text>
                        <div>
                          {item.course_code && <Tag color="blue" style={{ fontSize: 10 }}>{item.course_code}</Tag>}
                          <Tag color="cyan" style={{ fontSize: 10 }}>S{item.semester_number}</Tag>
                          <Text style={{ fontSize: 11, color: '#8c8c8c' }}>{item.ects_credits} ECTS</Text>
                        </div>
                      </div>
                      <Tag color="purple" style={{ margin: 0 }}>Level {item.level}</Tag>
                    </div>
                    {item.required_by_name && (
                      <div style={{ marginTop: 8, fontSize: 11, borderTop: '1px dashed #e8e8e8', paddingTop: 6 }}>
                        <Text type="secondary">Required directly by: </Text>
                        <Text strong>{item.required_by_name}</Text>
                      </div>
                    )}
                  </Card>
                )}
              />
            </div>
          )}
        </Spin>
      </Drawer>

      {/* Batch ECTS Modal */}
      <Modal
        title="Batch Update ECTS Credits"
        open={batchEctsModalOpen}
        onCancel={() => setBatchEctsModalOpen(false)}
        onOk={handleBatchUpdateEcts}
        okText="Update Selected"
        destroyOnClose
      >
        <Form layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item label={`Specify ECTS Credits for the ${selectedRowKeys.length} selected courses (1-30):`}>
            <InputNumber
              min={1}
              max={30}
              value={batchEctsValue}
              onChange={(val) => setBatchEctsValue(val)}
              style={{ width: '100%' }}
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* Batch Difficulty Modal */}
      <Modal
        title="Batch Update Difficulty Level"
        open={batchDifficultyModalOpen}
        onCancel={() => setBatchDifficultyModalOpen(false)}
        onOk={handleBatchUpdateDifficulty}
        okText="Update Selected"
        destroyOnClose
      >
        <Form layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item label={`Specify Difficulty Level for the ${selectedRowKeys.length} selected courses (1-5):`}>
            <Select value={batchDifficultyValue} onChange={(val) => setBatchDifficultyValue(val)} style={{ width: '100%' }}>
              {[1, 2, 3, 4, 5].map((n) => (
                <Option key={n} value={n}>
                  Level {n}
                </Option>
              ))}
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      {/* History Drawer */}
      <Drawer
        title="Course Change History"
        placement="right"
        width={480}
        onClose={() => {
          setHistoryDrawerOpen(false);
          setHistoryEntityId(null);
        }}
        open={historyDrawerOpen}
        destroyOnClose
      >
        <EntityHistory entityType="course" entityId={historyEntityId} />
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
            You have unsaved changes in one of the form editors or inline table editors. If you leave this page, your modifications will be lost.
          </Paragraph>
          <Paragraph type="secondary">
            Are you sure you want to discard your changes and navigate away?
          </Paragraph>
        </Modal>
      )}
    </div>
  );
};

export default Courses;
