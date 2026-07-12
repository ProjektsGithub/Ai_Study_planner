import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
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
  DatePicker,
  InputNumber,
  Descriptions,
  Result,
  message,
} from 'antd';
import {
  SearchOutlined,
  ReloadOutlined,
  DownloadOutlined,
  InfoCircleOutlined,
  HistoryOutlined,
  WarningOutlined,
} from '@ant-design/icons';
import { useAuth } from '../../context/AuthContext';

const { Title, Paragraph, Text } = Typography;
const { Option } = Select;
const { RangePicker } = DatePicker;

const AuditLogs = () => {
  const navigate = useNavigate();
  const { hasRole } = useAuth();
  const isSuperAdmin = hasRole('super_admin');

  // Table filters & paging states
  const [currentPage, setCurrentPage] = useState(() => {
    const val = sessionStorage.getItem('audit_page');
    return val ? parseInt(val, 10) : 1;
  });
  const [pageSize, setPageSize] = useState(25);
  const [selectedEntityType, setSelectedEntityType] = useState(() => sessionStorage.getItem('audit_entity_type') || undefined);
  const [selectedOperation, setSelectedOperation] = useState(() => sessionStorage.getItem('audit_operation') || undefined);
  const [filterUserId, setFilterUserId] = useState(() => {
    const val = sessionStorage.getItem('audit_user_id');
    return val ? parseInt(val, 10) : undefined;
  });
  const [dateRange, setDateRange] = useState(null);

  // Detail Modal states
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [activeLog, setActiveLog] = useState(null);
  const [isExporting, setIsExporting] = useState(false);

  // 1. Query audit logs (paginated & filtered)
  const {
    data: logsData,
    isLoading: isLogsLoading,
    refetch: refetchLogs,
  } = useQuery({
    queryKey: [
      'adminAuditLogsList',
      currentPage,
      pageSize,
      selectedEntityType,
      selectedOperation,
      filterUserId,
      dateRange,
    ],
    queryFn: async () => {
      const params = {
        page: currentPage,
        page_size: pageSize,
      };
      if (selectedEntityType) params.entity_type = selectedEntityType;
      if (selectedOperation) params.operation = selectedOperation;
      if (filterUserId) params.user_id = filterUserId;
      if (dateRange && dateRange[0]) params.start_date = dateRange[0].toISOString();
      if (dateRange && dateRange[1]) params.end_date = dateRange[1].toISOString();

      const response = await apiClient.get('/api/v1/admin/audit/logs', { params });
      return response.data;
    },
    enabled: isSuperAdmin,
  });

  // RBAC Guard - Audit logs are Super Admin only
  if (!isSuperAdmin) {
    return (
      <div style={{ padding: 24 }}>
        <Card style={{ borderRadius: 8, boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
          <Result
            status="403"
            title="403 Access Denied"
            subTitle="Sorry, only Super Administrators are authorized to inspect the system audit logs."
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

  // Handle Log Export (CSV or JSON blob download)
  const handleExport = async (format) => {
    setIsExporting(true);
    try {
      const params = { format };
      if (selectedEntityType) params.entity_type = selectedEntityType;
      if (selectedOperation) params.operation = selectedOperation;
      if (filterUserId) params.user_id = filterUserId;
      if (dateRange && dateRange[0]) params.start_date = dateRange[0].toISOString();
      if (dateRange && dateRange[1]) params.end_date = dateRange[1].toISOString();

      const response = await apiClient.get('/api/v1/admin/audit/logs/export', {
        params,
        responseType: 'blob',
      });

      const blob = new Blob([response.data], {
        type: format === 'csv' ? 'text/csv' : 'application/json',
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `audit_logs_${new Date().toISOString().slice(0, 10)}.${format}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      message.success(`Audit logs exported as ${format.toUpperCase()} successfully.`);
    } catch (err) {
      message.error('Failed to export audit logs.');
    } finally {
      setIsExporting(false);
    }
  };

  const showDetailsModal = (record) => {
    setActiveLog(record);
    setDetailModalOpen(true);
  };

  const operationTags = {
    create: <Tag color="green">CREATE</Tag>,
    update: <Tag color="blue">UPDATE</Tag>,
    delete: <Tag color="red">DELETE</Tag>,
  };

  const columns = [
    {
      title: 'Log ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
      render: (id) => <Text strong>#{id}</Text>,
    },
    {
      title: 'Timestamp',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 170,
      render: (ts) => {
        if (!ts) return <Text>—</Text>;
        const d = new Date(ts);
        const day = String(d.getDate()).padStart(2, '0');
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const year = d.getFullYear();
        const hrs = String(d.getHours()).padStart(2, '0');
        const mins = String(d.getMinutes()).padStart(2, '0');
        const secs = String(d.getSeconds()).padStart(2, '0');
        return <Text>{`${day}.${month}.${year} ${hrs}:${mins}:${secs}`}</Text>;
      },
    },
    {
      title: 'Operation',
      dataIndex: 'operation',
      key: 'operation',
      width: 110,
      render: (op) => operationTags[op] || <Tag>{op.toUpperCase()}</Tag>,
    },
    {
      title: 'Actor',
      dataIndex: 'user_email',
      key: 'user_email',
      width: 160,
      render: (email, record) => email || `User #${record.user_id}`,
    },
    {
      title: 'Entity Type',
      dataIndex: 'entity_type',
      key: 'entity_type',
      width: 130,
      render: (type) => <Tag color="orange">{type.toUpperCase()}</Tag>,
    },
    {
      title: 'Entity ID',
      dataIndex: 'entity_id',
      key: 'entity_id',
      width: 90,
      render: (id) => (id ? <Text code>{id}</Text> : '—'),
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: 'Action',
      key: 'action',
      width: 100,
      render: (_, record) => (
        <Button
          type="text"
          icon={<InfoCircleOutlined style={{ color: '#1890ff' }} />}
          onClick={() => showDetailsModal(record)}
        >
          Details
        </Button>
      ),
    },
  ];

  // Helper to render key-by-key changes list for update logs
  const renderFieldDiffs = (before, after) => {
    if (!before || !after) return <Text type="secondary">No field values available.</Text>;
    const diffs = [];

    // Keys to ignore for clean diff
    const ignoreKeys = ['updated_at', 'created_at', 'deleted_at', 'is_deleted'];

    // Identify changed fields
    Object.keys(after).forEach((key) => {
      if (ignoreKeys.includes(key)) return;
      const beforeVal = before[key];
      const afterVal = after[key];

      if (JSON.stringify(beforeVal) !== JSON.stringify(afterVal)) {
        diffs.push({
          field: key.replace('_', ' ').toUpperCase(),
          oldVal: beforeVal === null || beforeVal === undefined ? '—' : String(beforeVal),
          newVal: afterVal === null || afterVal === undefined ? '—' : String(afterVal),
        });
      }
    });

    if (diffs.length === 0) {
      return <Text type="secondary">No field mutations detected (audit snapshot metadata update only).</Text>;
    }

    return (
      <Table
        dataSource={diffs.map((d, i) => ({ ...d, key: i }))}
        size="small"
        pagination={false}
        bordered
        columns={[
          { title: 'FIELD', dataIndex: 'field', key: 'field', width: 140 },
          {
            title: 'BEFORE VALUE',
            dataIndex: 'oldVal',
            key: 'oldVal',
            render: (text) => <Text delete type="danger" style={{ background: '#fff1f0', padding: '2px 4px', borderRadius: 2 }}>{text}</Text>,
          },
          {
            title: 'AFTER VALUE',
            dataIndex: 'newVal',
            key: 'newVal',
            render: (text) => <Text type="success" style={{ background: '#f6ffed', padding: '2px 4px', borderRadius: 2, fontWeight: 500 }}>{text}</Text>,
          },
        ]}
      />
    );
  };

  return (
    <div style={{ padding: 24, background: '#fff', borderRadius: 8, minHeight: '100%' }}>
      {/* Header section */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16, marginBottom: 24 }}>
        <div>
          <Breadcrumb style={{ marginBottom: 8 }}>
            <Breadcrumb.Item><Link to="/admin/dashboard">Admin Platform</Link></Breadcrumb.Item>
            <Breadcrumb.Item>Audit Logs</Breadcrumb.Item>
          </Breadcrumb>
          <Title level={2} style={{ margin: 0 }}>System Audit Logs</Title>
          <Paragraph style={{ margin: 0, marginTop: 4 }}>
            Chronological log of administrative actions, curriculum updates, bulk imports, and system configuration mutations.
          </Paragraph>
        </div>

        <Space>
          <Button
            icon={<DownloadOutlined />}
            loading={isExporting}
            onClick={() => handleExport('csv')}
          >
            Export CSV
          </Button>
          <Button
            icon={<DownloadOutlined />}
            loading={isExporting}
            onClick={() => handleExport('json')}
          >
            Export JSON
          </Button>
        </Space>
      </div>

      {/* Advanced Filter Panel */}
      <Card style={{ marginBottom: 24, boxShadow: '0 1px 2px rgba(0,0,0,0.03)' }} bodyStyle={{ padding: '20px 24px' }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={12} md={5}>
            <Select
              style={{ width: '100%' }}
              placeholder="Entity Type"
              value={selectedEntityType}
              onChange={(val) => {
                setSelectedEntityType(val || undefined);
                if (val) {
                  sessionStorage.setItem('audit_entity_type', val);
                } else {
                  sessionStorage.removeItem('audit_entity_type');
                }
                setCurrentPage(1);
                sessionStorage.setItem('audit_page', '1');
              }}
              allowClear
            >
              {[
                'university',
                'campus',
                'study_program',
                'academic_track',
                'semester',
                'teaching_unit',
                'course',
                'prerequisite',
                'bulk_import',
                'validation_rule',
              ].map((type) => (
                <Option key={type} value={type}>
                  {type.toUpperCase().replace('_', ' ')}
                </Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} sm={12} md={4}>
            <Select
              style={{ width: '100%' }}
              placeholder="Operation"
              value={selectedOperation}
              onChange={(val) => {
                setSelectedOperation(val || undefined);
                if (val) {
                  sessionStorage.setItem('audit_operation', val);
                } else {
                  sessionStorage.removeItem('audit_operation');
                }
                setCurrentPage(1);
                sessionStorage.setItem('audit_page', '1');
              }}
              allowClear
            >
              <Option value="create">CREATE</Option>
              <Option value="update">UPDATE</Option>
              <Option value="delete">DELETE</Option>
            </Select>
          </Col>
          <Col xs={24} sm={12} md={4}>
            <InputNumber
              placeholder="Actor User ID"
              style={{ width: '100%' }}
              value={filterUserId}
              onChange={(val) => {
                setFilterUserId(val || undefined);
                if (val) {
                  sessionStorage.setItem('audit_user_id', String(val));
                } else {
                  sessionStorage.removeItem('audit_user_id');
                }
                setCurrentPage(1);
                sessionStorage.setItem('audit_page', '1');
              }}
              min={1}
            />
          </Col>
          <Col xs={24} sm={12} md={8}>
            <RangePicker
              style={{ width: '100%' }}
              value={dateRange}
              onChange={(val) => {
                setDateRange(val);
                setCurrentPage(1);
              }}
            />
          </Col>
          <Col xs={24} md={3} style={{ textAlign: 'right' }}>
            <Button
              icon={<ReloadOutlined />}
              onClick={() => {
                setSelectedEntityType(undefined);
                setSelectedOperation(undefined);
                setFilterUserId(undefined);
                setDateRange(null);
                setCurrentPage(1);
                sessionStorage.removeItem('audit_entity_type');
                sessionStorage.removeItem('audit_operation');
                sessionStorage.removeItem('audit_user_id');
                sessionStorage.setItem('audit_page', '1');
                refetchLogs();
              }}
            >
              Reset
            </Button>
          </Col>
        </Row>
      </Card>

      {/* Logs Table */}
      <Table
        scroll={{ x: 'max-content' }}
        columns={columns}
        dataSource={logsData?.logs || []}
        rowKey="id"
        loading={isLogsLoading}
        pagination={{
          current: currentPage,
          pageSize: pageSize,
          total: logsData?.total || 0,
          showSizeChanger: true,
          pageSizeOptions: ['10', '25', '50', '100', '200'],
          onChange: (p, ps) => {
            setCurrentPage(p);
            sessionStorage.setItem('audit_page', String(p));
            setPageSize(ps);
          },
        }}
        locale={{ emptyText: 'No audit logs found matching criteria.' }}
      />

      {/* Log Details Modal */}
      <Modal
        title={
          <Space>
            <HistoryOutlined />
            <span>Audit Log Detailed View: <Text strong>#{activeLog?.id}</Text></span>
          </Space>
        }
        open={detailModalOpen}
        onCancel={() => {
          setDetailModalOpen(false);
          setActiveLog(null);
        }}
        footer={[
          <Button
            key="close"
            onClick={() => {
              setDetailModalOpen(false);
              setActiveLog(null);
            }}
          >
            Close Window
          </Button>,
        ]}
        width={750}
        destroyOnClose
      >
        {activeLog && (
          <div style={{ marginTop: 16 }}>
            <Descriptions bordered column={2} size="small" style={{ marginBottom: 20 }}>
              <Descriptions.Item label="Log ID">#{activeLog.id}</Descriptions.Item>
              <Descriptions.Item label="Timestamp">
                {new Date(activeLog.timestamp).toLocaleString()}
              </Descriptions.Item>
              <Descriptions.Item label="Actor Email">
                {activeLog.user_email || `User #${activeLog.user_id}`}
              </Descriptions.Item>
              <Descriptions.Item label="Operation">
                {operationTags[activeLog.operation]}
              </Descriptions.Item>
              <Descriptions.Item label="Entity Type">
                <Tag color="orange">{activeLog.entity_type.toUpperCase()}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Entity ID">
                {activeLog.entity_id ? <Text code>{activeLog.entity_id}</Text> : '—'}
              </Descriptions.Item>
              <Descriptions.Item label="Description" span={2}>
                {activeLog.description}
              </Descriptions.Item>
            </Descriptions>

            {activeLog.operation === 'update' ? (
              <div>
                <Title level={5}>Field Mutations Details (Before vs. After):</Title>
                {renderFieldDiffs(activeLog.before_value, activeLog.after_value)}
              </div>
            ) : (
              <div>
                <Title level={5}>Entity Snapshot Content:</Title>
                <div
                  style={{
                    background: '#f8fafc',
                    padding: 12,
                    borderRadius: 4,
                    border: '1px solid #e2e8f0',
                    maxHeight: 250,
                    overflowY: 'auto',
                  }}
                >
                  <pre style={{ margin: 0, fontSize: 11 }}>
                    {JSON.stringify(
                      activeLog.operation === 'delete'
                        ? activeLog.before_value
                        : activeLog.after_value,
                      null,
                      2
                    )}
                  </pre>
                </div>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};

export default AuditLogs;
