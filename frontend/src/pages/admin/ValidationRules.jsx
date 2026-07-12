import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
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
  Alert,
  Spin,
  Tooltip,
  Divider,
  Popconfirm,
  message,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  InfoCircleOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { useAuth } from '../../context/AuthContext';

const { Title, Paragraph, Text } = Typography;
const { Option } = Select;

const ValidationRules = () => {
  const queryClient = useQueryClient();
  const { hasRole } = useAuth();
  const isSuperAdmin = hasRole('super_admin');
  const isCoordinator = hasRole('program_coordinator');
  const canEdit = isSuperAdmin || isCoordinator;

  // Selected Academic Track filter
  const [selectedTrackId, setSelectedTrackId] = useState(() => {
    const val = sessionStorage.getItem('rules_track_id');
    return val ? parseInt(val, 10) : undefined;
  });

  // Form modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [editingRule, setEditingRule] = useState(null);
  const [ruleForm] = Form.useForm();

  // 1. Fetch academic tracks for selector
  const { data: trackListData, isLoading: isTracksLoading } = useQuery({
    queryKey: ['allTracksList'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/admin/tracks?limit=200');
      return response.data;
    },
  });

  // 2. Fetch validation rules for selected track
  const {
    data: rulesData,
    isLoading: isRulesLoading,
    refetch: refetchRules,
  } = useQuery({
    queryKey: ['adminValidationRules', selectedTrackId],
    queryFn: async () => {
      if (!selectedTrackId) return { rules: [], total: 0 };
      const response = await apiClient.get('/api/v1/admin/validation-rules', {
        params: { academic_track_id: selectedTrackId, limit: 100 },
      });
      return response.data;
    },
    enabled: !!selectedTrackId,
  });

  // 3. Fetch ECTS hierarchy validation status for selected track
  const {
    data: hierarchyStatus,
    isLoading: isHierarchyLoading,
    refetch: refetchHierarchy,
  } = useQuery({
    queryKey: ['ectsHierarchyStatus', selectedTrackId],
    queryFn: async () => {
      if (!selectedTrackId) return null;
      const response = await apiClient.get(
        `/api/v1/admin/validation-rules/track/${selectedTrackId}/validate-ects`
      );
      return response.data;
    },
    enabled: !!selectedTrackId,
  });

  // 4. Mutations
  const createRuleMutation = useMutation({
    mutationFn: async (values) => {
      const response = await apiClient.post('/api/v1/admin/validation-rules', values);
      return response.data;
    },
    onSuccess: () => {
      message.success('Validation rule created successfully.');
      setModalOpen(false);
      ruleForm.resetFields();
      queryClient.invalidateQueries({ queryKey: ['adminValidationRules', selectedTrackId] });
      queryClient.invalidateQueries({ queryKey: ['ectsHierarchyStatus', selectedTrackId] });
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || 'Failed to create validation rule.');
    },
  });

  const updateRuleMutation = useMutation({
    mutationFn: async ({ id, values }) => {
      const response = await apiClient.put(`/api/v1/admin/validation-rules/${id}`, values);
      return response.data;
    },
    onSuccess: () => {
      message.success('Validation rule updated successfully.');
      setModalOpen(false);
      setEditingRule(null);
      ruleForm.resetFields();
      queryClient.invalidateQueries({ queryKey: ['adminValidationRules', selectedTrackId] });
      queryClient.invalidateQueries({ queryKey: ['ectsHierarchyStatus', selectedTrackId] });
    },
    onError: (error) => {
      const detail = error.response?.data?.detail;
      // Handle the FastAPI 400 hierarchy violation error payload
      if (detail && detail.hierarchy_errors) {
        Modal.warning({
          title: 'ECTS Hierarchy Constraint Warning',
          icon: <WarningOutlined style={{ color: '#faad14' }} />,
          content: (
            <div>
              <Paragraph>{detail.message}</Paragraph>
              <ul style={{ paddingLeft: 16 }}>
                {detail.hierarchy_errors.map((err, i) => (
                  <li key={i}><Text type="danger">{err}</Text></li>
                ))}
              </ul>
              <Paragraph style={{ marginTop: 12 }}>
                The changes were saved, but you should adjust the ECTS limits to establish a valid progression hierarchy.
              </Paragraph>
            </div>
          ),
          onOk: () => {
            setModalOpen(false);
            setEditingRule(null);
            ruleForm.resetFields();
            queryClient.invalidateQueries({ queryKey: ['adminValidationRules', selectedTrackId] });
            queryClient.invalidateQueries({ queryKey: ['ectsHierarchyStatus', selectedTrackId] });
          },
        });
      } else {
        message.error(error.response?.data?.detail || 'Failed to update validation rule.');
      }
    },
  });

  const deleteRuleMutation = useMutation({
    mutationFn: async (id) => {
      const response = await apiClient.delete(`/api/v1/admin/validation-rules/${id}`);
      return response.data;
    },
    onSuccess: () => {
      message.success('Validation rule deleted successfully.');
      queryClient.invalidateQueries({ queryKey: ['adminValidationRules', selectedTrackId] });
      queryClient.invalidateQueries({ queryKey: ['ectsHierarchyStatus', selectedTrackId] });
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || 'Failed to delete validation rule.');
    },
  });

  const trackMap = {};
  trackListData?.tracks?.forEach((t) => {
    trackMap[t.id] = t;
  });

  // Calculate rule types currently present to filter the Add modal dropdown options
  const presentRuleTypes = rulesData?.rules?.map((r) => r.rule_type) || [];
  const ruleTypeOptions = [
    { value: 'semester_validation', label: 'Semester Validation' },
    { value: 'year_progression', label: 'Year Progression' },
    { value: 'graduation', label: 'Graduation Requirement' },
  ].filter((opt) => editingRule || !presentRuleTypes.includes(opt.value));

  const handleFormSubmit = (values) => {
    const payload = {
      ...values,
      academic_track_id: selectedTrackId,
      minimum_ects: parseInt(values.minimum_ects, 10),
    };

    if (editingRule) {
      updateRuleMutation.mutate({ id: editingRule.id, values: payload });
    } else {
      createRuleMutation.mutate(payload);
    }
  };

  const showCreateModal = () => {
    setEditingRule(null);
    ruleForm.resetFields();
    ruleForm.setFieldsValue({ minimum_ects: 30 });
    setModalOpen(true);
  };

  const showEditModal = (record) => {
    setEditingRule(record);
    ruleForm.setFieldsValue({
      rule_type: record.rule_type,
      name: record.name,
      name_de: record.name_de,
      minimum_ects: record.minimum_ects,
      description: record.description,
      description_de: record.description_de,
      additional_conditions: record.additional_conditions,
      additional_conditions_de: record.additional_conditions_de,
    });
    setModalOpen(true);
  };

  const ruleTypeTags = {
    semester_validation: <Tag color="blue">SEMESTER VALIDATION</Tag>,
    year_progression: <Tag color="orange">YEAR PROGRESSION</Tag>,
    graduation: <Tag color="purple">GRADUATION</Tag>,
  };

  const columns = [
    {
      title: 'Rule Type',
      dataIndex: 'rule_type',
      key: 'rule_type',
      width: 200,
      render: (type) => ruleTypeTags[type] || <Tag>{type.toUpperCase()}</Tag>,
    },
    {
      title: 'Rule Name',
      key: 'rule_name',
      render: (_, record) => (
        <Space direction="vertical" size={0}>
          <Text strong style={{ fontSize: 13 }}>{record.name}</Text>
          {record.name_de && (
            <Text type="secondary" style={{ fontSize: 11 }}>DE: {record.name_de}</Text>
          )}
        </Space>
      ),
    },
    {
      title: 'Min ECTS Required',
      dataIndex: 'minimum_ects',
      key: 'minimum_ects',
      width: 160,
      render: (ects) => <Text strong>{ects} ECTS</Text>,
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 120,
      render: (_, record) => (
        <Space size={8}>
          {canEdit && (
            <Tooltip title="Edit Rule">
              <Button
                type="text"
                icon={<EditOutlined style={{ color: '#1890ff' }} />}
                onClick={() => showEditModal(record)}
              />
            </Tooltip>
          )}
          {isSuperAdmin && (
            <Popconfirm
              title="Delete this validation rule?"
              onConfirm={() => deleteRuleMutation.mutate(record.id)}
              okText="Yes"
              cancelText="No"
              okButtonProps={{ danger: true }}
            >
              <Tooltip title="Delete Rule">
                <Button
                  type="text"
                  icon={<DeleteOutlined style={{ color: '#f5222d' }} />}
                />
              </Tooltip>
            </Popconfirm>
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
            <Breadcrumb.Item>Validation Rules</Breadcrumb.Item>
          </Breadcrumb>
          <Title level={2} style={{ margin: 0 }}>ECTS Validation Rules</Title>
          <Paragraph style={{ margin: 0, marginTop: 4 }}>
            Configure credit boundaries required for semester validation, year progression, and graduation criteria per academic track.
          </Paragraph>
        </div>

        {canEdit && selectedTrackId && ruleTypeOptions.length > 0 && (
          <Button type="primary" icon={<PlusOutlined />} onClick={showCreateModal}>
            Add Rule
          </Button>
        )}
      </div>

      {/* Select Track Panel */}
      <Card style={{ marginBottom: 24, boxShadow: '0 1px 2px rgba(0,0,0,0.03)' }} bodyStyle={{ padding: '16px 24px' }}>
        <Row gutter={16} align="middle">
          <Col xs={24} md={12}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <span style={{ fontWeight: 'bold', whiteSpace: 'nowrap' }}>Choose Academic Track:</span>
              <Select
                style={{ width: '100%' }}
                placeholder="Select an academic track to configure..."
                value={selectedTrackId}
                onChange={(val) => {
                  setSelectedTrackId(val || undefined);
                  if (val) {
                    sessionStorage.setItem('rules_track_id', String(val));
                  } else {
                    sessionStorage.removeItem('rules_track_id');
                  }
                }}
                loading={isTracksLoading}
                allowClear
              >
                {trackListData?.tracks?.map((t) => (
                  <Option key={t.id} value={t.id}>
                    {t.name} ({t.level})
                  </Option>
                ))}
              </Select>
            </div>
          </Col>
          <Col xs={24} md={12} style={{ textAlign: 'right' }}>
            {selectedTrackId && (
              <Button
                icon={<ReloadOutlined />}
                onClick={() => {
                  refetchRules();
                  refetchHierarchy();
                }}
              >
                Sync Rules Status
              </Button>
            )}
          </Col>
        </Row>
      </Card>

      {!selectedTrackId ? (
        <Alert
          message="No Track Selected"
          description="Please select an academic track above to view and configure its validation parameters."
          type="info"
          showIcon
        />
      ) : (
        <Row gutter={[24, 24]}>
          {/* Main List */}
          <Col xs={24} lg={16}>
            <Table
              scroll={{ x: 'max-content' }}
              columns={columns}
              dataSource={rulesData?.rules || []}
              rowKey="id"
              loading={isRulesLoading}
              pagination={false}
              locale={{ emptyText: 'No validation rules configured for this track yet.' }}
            />
          </Col>

          {/* Validation Status Panel */}
          <Col xs={24} lg={8}>
            <Card title="ECTS Hierarchy Status" style={{ height: '100%', boxShadow: '0 1px 2px rgba(0,0,0,0.02)' }}>
              <Spin spinning={isHierarchyLoading}>
                {hierarchyStatus && (
                  <div>
                    {/* Visual boundaries flow */}
                    <div
                      style={{
                        padding: '16px',
                        background: '#f8fafc',
                        borderRadius: 8,
                        marginBottom: 20,
                        border: '1px solid #e2e8f0',
                        textAlign: 'center',
                      }}
                    >
                      <Paragraph style={{ margin: 0, fontSize: 13, color: '#64748b' }}>
                        Hierarchy Progression Flow Constraints
                      </Paragraph>
                      <div style={{ marginTop: 12, display: 'flex', justifyContent: 'center', gap: 8, alignItems: 'center' }}>
                        <Tooltip title="Graduation ECTS Limit">
                          <Tag color="purple" style={{ fontSize: 13, padding: '4px 8px' }}>
                            🎓 {hierarchyStatus.graduation_ects ?? '—'}
                          </Tag>
                        </Tooltip>
                        <Text strong>&ge;</Text>
                        <Tooltip title="Year Progression ECTS Limit">
                          <Tag color="orange" style={{ fontSize: 13, padding: '4px 8px' }}>
                            📅 {hierarchyStatus.year_progression_ects ?? '—'}
                          </Tag>
                        </Tooltip>
                        <Text strong>&ge;</Text>
                        <Tooltip title="Semester Validation ECTS Limit">
                          <Tag color="blue" style={{ fontSize: 13, padding: '4px 8px' }}>
                            ⏱️ {hierarchyStatus.semester_validation_ects ?? '—'}
                          </Tag>
                        </Tooltip>
                      </div>
                    </div>

                    {hierarchyStatus.is_valid ? (
                      <Alert
                        message="Status: Valid"
                        description="The ECTS rules sequence matches hierarchy conditions correctly."
                        type="success"
                        showIcon
                        icon={<CheckCircleOutlined />}
                      />
                    ) : (
                      <Alert
                        message="Status: Conflict Detected"
                        description={
                          <div style={{ marginTop: 6 }}>
                            <Paragraph style={{ margin: 0, fontSize: 12 }}>
                              The current configuration violates progression constraints:
                            </Paragraph>
                            <ul style={{ paddingLeft: 16, marginTop: 4, margin: 0, fontSize: 12 }}>
                              {hierarchyStatus.errors?.map((err, i) => (
                                <li key={i}><Text type="danger">{err}</Text></li>
                              ))}
                            </ul>
                          </div>
                        }
                        type="warning"
                        showIcon
                        icon={<WarningOutlined />}
                      />
                    )}

                    <Divider />
                    <Paragraph style={{ fontSize: 12, color: '#8c8c8c', margin: 0 }}>
                      <InfoCircleOutlined /> To resolve constraint violations, edit the respective rules so that Graduation requirement credits are greater than or equal to Year Progression requirements, which in turn must be greater than or equal to individual Semester thresholds.
                    </Paragraph>
                  </div>
                )}
              </Spin>
            </Card>
          </Col>
        </Row>
      )}

      {/* Add/Edit Modal */}
      <Modal
        title={editingRule ? 'Edit ECTS Validation Rule' : 'Create ECTS Validation Rule'}
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        footer={null}
        destroyOnClose
        width={600}
      >
        <Form
          form={ruleForm}
          layout="vertical"
          onFinish={handleFormSubmit}
          style={{ marginTop: 16 }}
        >
          <Row gutter={16}>
            <Col span={14}>
              <Form.Item
                name="rule_type"
                label="Rule Type"
                rules={[{ required: true, message: 'Please select rule type' }]}
              >
                <Select placeholder="Select type..." disabled={!!editingRule}>
                  {ruleTypeOptions.map((opt) => (
                    <Option key={opt.value} value={opt.value}>
                      {opt.label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={10}>
              <Form.Item
                name="minimum_ects"
                label="Minimum ECTS Limit"
                rules={[
                  { required: true, message: 'Required' },
                  {
                    validator: (_, val) => {
                      if (val !== undefined && val !== null && (isNaN(val) || parseInt(val, 10) < 1)) {
                        return Promise.reject(new Error('Must be positive number'));
                      }
                      return Promise.resolve();
                    },
                  },
                ]}
              >
                <Input type="number" min={1} placeholder="e.g. 180" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="name"
            label="Rule Title (English)"
            rules={[
              { required: true, message: 'Title is required' },
              { max: 255, message: 'Must be 255 characters or less' },
            ]}
          >
            <Input placeholder="e.g. Bachelor Graduation limit" />
          </Form.Item>

          <Form.Item
            name="name_de"
            label="Rule Title (German)"
            rules={[{ max: 255, message: 'Must be 255 characters or less' }]}
          >
            <Input placeholder="e.g. Bachelor-Graduierungsgrenze" />
          </Form.Item>

          <Form.Item name="description" label="English Description">
            <Input.TextArea rows={2} placeholder="Explain ECTS validation criteria..." />
          </Form.Item>

          <Form.Item name="description_de" label="German Description">
            <Input.TextArea rows={2} placeholder="Beschreibung auf Deutsch..." />
          </Form.Item>

          <Form.Item name="additional_conditions" label="Additional English Conditions (Optional)">
            <Input.TextArea rows={2} placeholder="Shorthand condition details e.g., thesis required" />
          </Form.Item>

          <Form.Item name="additional_conditions_de" label="Additional German Conditions (Optional)">
            <Input.TextArea rows={2} placeholder="Abschlussbedingungen auf Deutsch..." />
          </Form.Item>

          <Form.Item style={{ textAlign: 'right', marginBottom: 0, marginTop: 24 }}>
            <Space>
              <Button onClick={() => setModalOpen(false)}>Cancel</Button>
              <Button
                type="primary"
                htmlType="submit"
                loading={createRuleMutation.isPending || updateRuleMutation.isPending}
              >
                {editingRule ? 'Save Changes' : 'Create Rule'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ValidationRules;
