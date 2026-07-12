import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '../../api/client';
import {
  Table,
  Button,
  Card,
  Typography,
  Breadcrumb,
  Space,
  Spin,
  Modal,
  Tag,
  Divider,
  Result,
  Row,
  Col,
  Descriptions,
  message,
} from 'antd';
import {
  HistoryOutlined,
  WarningOutlined,
  ReloadOutlined,
  ArrowLeftOutlined,
  UndoOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import { useAuth } from '../../context/AuthContext';

const { Title, Paragraph, Text } = Typography;

const ImportHistory = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { hasRole } = useAuth();
  const isSuperAdmin = hasRole('super_admin');

  // Pagination states
  const [currentPage, setCurrentPage] = useState(() => {
    const val = sessionStorage.getItem('imports_history_page');
    return val ? parseInt(val, 10) : 1;
  });
  const [pageSize, setPageSize] = useState(10);

  // Detail Modal states
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [activeImportId, setActiveImportId] = useState(null);

  // 1. Fetch import history
  const {
    data: historyData,
    isLoading: isHistoryLoading,
    refetch: refetchHistory,
  } = useQuery({
    queryKey: ['adminImportHistory', currentPage, pageSize],
    queryFn: async () => {
      const skip = (currentPage - 1) * pageSize;
      const response = await apiClient.get('/api/v1/admin/imports', {
        params: { skip, limit: pageSize },
      });
      return response.data;
    },
    enabled: isSuperAdmin,
  });

  // 2. Fetch specific import details
  const { data: importDetails, isLoading: isDetailsLoading } = useQuery({
    queryKey: ['adminImportDetail', activeImportId],
    queryFn: async () => {
      if (!activeImportId) return null;
      const response = await apiClient.get(`/api/v1/admin/imports/${activeImportId}`);
      return response.data;
    },
    enabled: !!activeImportId && detailModalOpen,
  });

  // 3. Rollback mutation
  const rollbackMutation = useMutation({
    mutationFn: async (importId) => {
      const response = await apiClient.post(`/api/v1/admin/imports/${importId}/rollback`);
      return response.data;
    },
    onSuccess: (data) => {
      Modal.success({
        title: 'Rollback Completed',
        content: (
          <div>
            <Paragraph>{data.message}</Paragraph>
            <Title level={5}>Soft-deleted counts:</Title>
            <ul style={{ paddingLeft: 16 }}>
              {Object.entries(data.deleted_counts || {}).map(([entity, count]) => (
                <li key={entity}>
                  {entity.toUpperCase()}: <Text strong>{String(count)}</Text>
                </li>
              ))}
            </ul>
          </div>
        ),
      });
      queryClient.invalidateQueries({ queryKey: ['adminImportHistory'] });
      queryClient.invalidateQueries({ queryKey: ['adminCoursesGlobal'] });
      queryClient.invalidateQueries({ queryKey: ['adminSemestersGlobal'] });
      queryClient.invalidateQueries({ queryKey: ['adminTeachingUnitsGlobal'] });
    },
    onError: (error) => {
      message.error(error.response?.data?.detail || 'Failed to rollback import session.');
    },
  });

  // RBAC Guard
  if (!isSuperAdmin) {
    return (
      <div style={{ padding: 24 }}>
        <Card style={{ borderRadius: 8, boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
          <Result
            status="403"
            title="403 Access Denied"
            subTitle="Sorry, only Super Administrators are authorized to view curriculum import transaction history."
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

  const showDetails = (id) => {
    setActiveImportId(id);
    setDetailModalOpen(true);
  };

  const handleRollbackConfirm = (record) => {
    Modal.confirm({
      title: 'Confirm Import Rollback',
      icon: <WarningOutlined style={{ color: '#f5222d' }} />,
      content: (
        <div>
          <Paragraph>
            Are you sure you want to roll back import session <Text strong>#{record.id}</Text>?
          </Paragraph>
          <Paragraph type="secondary">
            This action will soft-delete all database records (universities, campuses, programs, tracks, semesters, teaching units, and courses) that were created by this specific Excel spreadsheet upload. This is a mutating rollback operation.
          </Paragraph>
        </div>
      ),
      okText: 'Yes, Rollback All',
      okButtonProps: { danger: true, loading: rollbackMutation.isPending },
      onOk: () => {
        return rollbackMutation.mutateAsync(record.id);
      },
    });
  };

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 70,
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
      title: 'Admin User ID',
      dataIndex: 'user_id',
      key: 'user_id',
      width: 120,
      render: (uid) => <Tag color="blue">User #{uid}</Tag>,
    },
    {
      title: 'Committed Summary',
      dataIndex: 'description',
      key: 'description',
      render: (desc, record) => {
        const counts = record.created_counts || {};
        return (
          <Space direction="vertical" size={4}>
            <Text style={{ fontSize: 13 }}>{desc}</Text>
            <Space size={[4, 4]} wrap>
              {Object.entries(counts).map(([ent, cnt]) => {
                if (cnt === 0) return null;
                return (
                  <Tag color="cyan" key={ent} style={{ fontSize: 10, margin: 0 }}>
                    {ent}: {String(cnt)}
                  </Tag>
                );
              })}
            </Space>
          </Space>
        );
      },
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 160,
      render: (_, record) => (
        <Space size={8}>
          <Button
            type="text"
            icon={<InfoCircleOutlined style={{ color: '#1890ff' }} />}
            onClick={() => showDetails(record.id)}
          >
            Details
          </Button>
          <Button
            type="text"
            danger
            icon={<UndoOutlined />}
            onClick={() => handleRollbackConfirm(record)}
          >
            Rollback
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: 24, background: '#fff', borderRadius: 8, minHeight: '100%' }}>
      {/* Header breadcrumb */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16, marginBottom: 24 }}>
        <div>
          <Breadcrumb style={{ marginBottom: 8 }}>
            <Breadcrumb.Item><Link to="/admin/dashboard">Admin Platform</Link></Breadcrumb.Item>
            <Breadcrumb.Item><Link to="/admin/imports">Bulk Import</Link></Breadcrumb.Item>
            <Breadcrumb.Item>Import History</Breadcrumb.Item>
          </Breadcrumb>
          <Title level={2} style={{ margin: 0 }}>Import Transaction History</Title>
          <Paragraph style={{ margin: 0, marginTop: 4 }}>
            Review past curriculum spreadsheet uploads, inspect created objects, and trigger atomic rollback transactions to remove erroneous batch writes.
          </Paragraph>
        </div>

        <Button
          type="primary"
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/admin/imports')}
        >
          Curriculum Import Wizard
        </Button>
      </div>

      {/* Control panel */}
      <Card style={{ marginBottom: 24, boxShadow: '0 1px 2px rgba(0,0,0,0.03)' }} bodyStyle={{ padding: '12px 24px' }}>
        <Row align="middle" justify="space-between">
          <Text type="secondary">
            Click Rollback to soft-delete all items created in a specific transaction timestamp window.
          </Text>
          <Button icon={<ReloadOutlined />} onClick={() => refetchHistory()}>
            Reload History
          </Button>
        </Row>
      </Card>

      {/* History table */}
      <Table
        scroll={{ x: 'max-content' }}
        dataSource={historyData?.imports || []}
        columns={columns}
        rowKey="id"
        loading={isHistoryLoading}
        pagination={{
          current: currentPage,
          pageSize: pageSize,
          total: historyData?.total || 0,
          showSizeChanger: true,
          pageSizeOptions: ['5', '10', '25', '50'],
          onChange: (p, ps) => {
            setCurrentPage(p);
            sessionStorage.setItem('imports_history_page', String(p));
            setPageSize(ps);
          },
        }}
        locale={{ emptyText: 'No past imports found in audit log registry.' }}
      />

      {/* Details Modal */}
      <Modal
        title={
          <Space>
            <HistoryOutlined />
            <span>Curriculum Import Details: <Text strong>#{activeImportId}</Text></span>
          </Space>
        }
        open={detailModalOpen}
        onCancel={() => {
          setDetailModalOpen(false);
          setActiveImportId(null);
        }}
        footer={[
          <Button
            key="close"
            onClick={() => {
              setDetailModalOpen(false);
              setActiveImportId(null);
            }}
          >
            Close Window
          </Button>,
        ]}
        width={600}
        destroyOnClose
      >
        <Spin spinning={isDetailsLoading}>
          {importDetails && (
            <div style={{ marginTop: 16 }}>
              <Descriptions bordered column={1} size="small">
                <Descriptions.Item label="Import ID">#{importDetails.id}</Descriptions.Item>
                <Descriptions.Item label="Committed Time">
                  {(() => {
                    const d = new Date(importDetails.timestamp);
                    const day = String(d.getDate()).padStart(2, '0');
                    const month = String(d.getMonth() + 1).padStart(2, '0');
                    const year = d.getFullYear();
                    const hrs = String(d.getHours()).padStart(2, '0');
                    const mins = String(d.getMinutes()).padStart(2, '0');
                    const secs = String(d.getSeconds()).padStart(2, '0');
                    return `${day}.${month}.${year} ${hrs}:${mins}:${secs}`;
                  })()}
                </Descriptions.Item>
                <Descriptions.Item label="Committed By">User #{importDetails.user_id}</Descriptions.Item>
                <Descriptions.Item label="Filename">
                  <Text code>{importDetails.filename || 'upload.xlsx'}</Text>
                </Descriptions.Item>
                <Descriptions.Item label="Upload Session Token">
                  <Text style={{ fontSize: 11 }}>{importDetails.session_id}</Text>
                </Descriptions.Item>
                <Descriptions.Item label="Total Entities Created">
                  <Text strong>{importDetails.total_created} records</Text>
                </Descriptions.Item>
              </Descriptions>

              <Divider style={{ margin: '16px 0' }} />
              <Title level={5}>Committed Object Breakdown:</Title>
              <Row gutter={[16, 12]}>
                {Object.entries(importDetails.created_counts || {}).map(([entity, count]) => (
                  <Col span={8} key={entity}>
                    <Text type="secondary">{entity.toUpperCase()}: </Text>
                    <Text strong>{String(count)}</Text>
                  </Col>
                ))}
              </Row>
            </div>
          )}
        </Spin>
      </Modal>
    </div>
  );
};

export default ImportHistory;
