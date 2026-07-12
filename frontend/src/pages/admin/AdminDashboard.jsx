import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import apiClient from '../../api/client';
import {
  Table,
  Tag,
  Button,
  Row,
  Col,
  Card,
  Statistic,
  Alert,
  Typography,
  Breadcrumb,
  Progress,
  Space,
  Spin,
  Tooltip,
} from 'antd';
import {
  BankOutlined,
  BookOutlined,
  ReadOutlined,
  BranchesOutlined,
  ReloadOutlined,
  DatabaseOutlined,
  HddOutlined,
  ApiOutlined,
  UserOutlined,
  HistoryOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  CloseCircleOutlined,
  QuestionCircleOutlined,
  CalendarOutlined,
  PartitionOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  ImportOutlined,
} from '@ant-design/icons';
import { useAuth } from '../../context/AuthContext';

const { Title, Paragraph, Text } = Typography;

const AdminDashboard = () => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  // 1. Fetch aggregate dashboard stats
  const {
    data: stats,
    isLoading: isStatsLoading,
    isError: isStatsError,
    refetch: refetchStats,
  } = useQuery({
    queryKey: ['adminDashboardStats'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/admin/dashboard/stats');
      return response.data;
    },
  });

  // 2. Fetch system health check
  const {
    data: health,
    isLoading: isHealthLoading,
    isError: isHealthError,
    refetch: refetchHealth,
  } = useQuery({
    queryKey: ['adminDashboardHealth'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/admin/dashboard/health');
      return response.data;
    },
    refetchInterval: 30000, // Refresh health status every 30 seconds
  });

  // 3. Fetch recent activities (paginated)
  const {
    data: activitiesData,
    isLoading: isActivitiesLoading,
    isError: isActivitiesError,
    refetch: refetchActivities,
  } = useQuery({
    queryKey: ['adminDashboardActivities', page, pageSize],
    queryFn: async () => {
      const skip = (page - 1) * pageSize;
      const response = await apiClient.get(
        `/api/v1/admin/dashboard/activities?skip=${skip}&limit=${pageSize}`
      );
      return response.data;
    },
  });

  // Trigger invalidation/refresh of all dashboard queries
  const handleRefresh = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ['adminDashboardStats'] }),
      queryClient.invalidateQueries({ queryKey: ['adminDashboardHealth'] }),
      queryClient.invalidateQueries({ queryKey: ['adminDashboardActivities'] }),
    ]);
  };

  const isGlobalLoading = isStatsLoading || isHealthLoading || isActivitiesLoading;

  // Helper to determine operation color tags
  const getOperationTag = (operation) => {
    switch (operation) {
      case 'create':
        return <Tag color="green">CREATE</Tag>;
      case 'update':
        return <Tag color="blue">UPDATE</Tag>;
      case 'delete':
        return <Tag color="red">DELETE</Tag>;
      default:
        return <Tag color="default">{operation.toUpperCase()}</Tag>;
    }
  };

  // Helper to retrieve health icons and colors
  const getHealthStatusProps = (status) => {
    switch (status) {
      case 'ok':
        return {
          icon: <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 20 }} />,
          tagColor: 'success',
          textClass: 'text-green-600',
        };
      case 'warning':
      case 'degraded':
        return {
          icon: <ExclamationCircleOutlined style={{ color: '#faad14', fontSize: 20 }} />,
          tagColor: 'warning',
          textClass: 'text-amber-500',
        };
      case 'error':
        return {
          icon: <CloseCircleOutlined style={{ color: '#f5222d', fontSize: 20 }} />,
          tagColor: 'error',
          textClass: 'text-red-600',
        };
      default:
        return {
          icon: <QuestionCircleOutlined style={{ color: '#bfbfbf', fontSize: 20 }} />,
          tagColor: 'default',
          textClass: 'text-gray-500',
        };
    }
  };

  // Table columns definition for activities
  const activityColumns = [
    {
      title: 'Action Description',
      dataIndex: 'description',
      key: 'description',
      render: (text, record) => (
        <Space direction="vertical" size={2}>
          <Text strong style={{ fontSize: 13 }}>{text || 'Admin Action'}</Text>
          <Text type="secondary" style={{ fontSize: 11 }}>
            Entity: <Text code>{record.entity_type}</Text> (ID: {record.entity_id})
          </Text>
        </Space>
      ),
    },
    {
      title: 'Operation',
      dataIndex: 'operation',
      key: 'operation',
      width: 110,
      render: (op) => getOperationTag(op),
    },
    {
      title: 'Actor',
      dataIndex: 'user_email',
      key: 'user_email',
      render: (email) => (
        <Space size={6}>
          <UserOutlined style={{ color: '#8c8c8c' }} />
          <Text style={{ fontSize: 13 }}>{email || 'System / Seed'}</Text>
        </Space>
      ),
    },
    {
      title: 'Timestamp',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 180,
      render: (dateStr) => {
        const date = new Date(dateStr);
        const day = String(date.getDate()).padStart(2, '0');
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const year = date.getFullYear();
        const hrs = String(date.getHours()).padStart(2, '0');
        const mins = String(date.getMinutes()).padStart(2, '0');
        const secs = String(date.getSeconds()).padStart(2, '0');
        const formatted = `${day}.${month}.${year} ${hrs}:${mins}:${secs}`;
        return (
          <Tooltip title={date.toString()}>
            <Text style={{ fontSize: 12 }}>
              {formatted}
            </Text>
          </Tooltip>
        );
      },
    },
  ];

  if (isStatsError || isHealthError || isActivitiesError) {
    return (
      <div style={{ padding: '24px' }}>
        <Alert
          message="Communication Error"
          description="Failed to retrieve latest monitoring statistics and metrics from the backend API. Please make sure the local server is running."
          type="error"
          showIcon
          action={
            <Button size="small" type="primary" icon={<ReloadOutlined />} onClick={handleRefresh}>
              Retry Connection
            </Button>
          }
        />
      </div>
    );
  }

  // Parse psutil percent value for progress visual if present
  const getMemoryUsagePercent = (healthItem) => {
    if (!healthItem || !healthItem.value) return 0;
    const match = healthItem.value.match(/(\d+(?:\.\d+)?)%\s+used/);
    return match ? parseFloat(match[1]) : 0;
  };

  const getDiskUsagePercent = (healthItem) => {
    if (!healthItem || !healthItem.value) return 0;
    const match = healthItem.value.match(/(\d+(?:\.\d+)?)%\s+used/);
    return match ? parseFloat(match[1]) : 0;
  };

  const dbCheck = health?.checks?.find((c) => c.name === 'database');
  const diskCheck = health?.checks?.find((c) => c.name === 'disk_space');
  const memCheck = health?.checks?.find((c) => c.name === 'memory');

  const overallHealthProps = getHealthStatusProps(health?.status);

  return (
    <div style={{ padding: '24px', background: '#fff', borderRadius: 8, minHeight: '100%' }}>
      {/* Breadcrumbs & Header Panel */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16, marginBottom: 24 }}>
        <div>
          <Breadcrumb style={{ marginBottom: 8 }}>
            <Breadcrumb.Item><Link to="/admin/dashboard">Admin Platform</Link></Breadcrumb.Item>
            <Breadcrumb.Item>Dashboard</Breadcrumb.Item>
          </Breadcrumb>
          <Title level={2} style={{ margin: 0 }}>Dashboard & Monitoring</Title>
          <Paragraph style={{ margin: 0, marginTop: 4 }}>
            Overview of the curriculum structures, AI generators, and hardware metrics.
          </Paragraph>
        </div>

        <Button
          type="primary"
          icon={<ReloadOutlined spin={isGlobalLoading} />}
          onClick={handleRefresh}
          disabled={isGlobalLoading}
        >
          {isGlobalLoading ? 'Refreshing...' : 'Refresh Metrics'}
        </Button>
      </div>

      {/* Overview Stat Widgets */}
      <Spin spinning={isStatsLoading}>
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={24} sm={12} lg={6}>
            <Card
              hoverable
              bordered={false}
              style={{
                boxShadow: '0 2px 10px rgba(0,0,0,0.04)',
                borderTop: '3px solid #1890ff',
              }}
            >
              <Statistic
                title="Active Universities"
                value={stats?.universities ?? 0}
                valueStyle={{ color: '#1890ff', fontWeight: 'bold' }}
                prefix={<BankOutlined style={{ marginRight: 8 }} />}
                suffix={
                  <span style={{ fontSize: 12, color: '#8c8c8c', marginLeft: 8 }}>
                    ({stats?.campuses ?? 0} campuses)
                  </span>
                }
              />
            </Card>
          </Col>

          <Col xs={24} sm={12} lg={6}>
            <Card
              hoverable
              bordered={false}
              style={{
                boxShadow: '0 2px 10px rgba(0,0,0,0.04)',
                borderTop: '3px solid #52c41a',
              }}
            >
              <Statistic
                title="Curriculum Programs"
                value={stats?.curriculum?.study_programs ?? 0}
                valueStyle={{ color: '#52c41a', fontWeight: 'bold' }}
                prefix={<BookOutlined style={{ marginRight: 8 }} />}
                suffix={
                  <span style={{ fontSize: 12, color: '#8c8c8c', marginLeft: 8 }}>
                    ({stats?.curriculum?.academic_tracks ?? 0} tracks)
                  </span>
                }
              />
            </Card>
          </Col>

          <Col xs={24} sm={12} lg={6}>
            <Card
              hoverable
              bordered={false}
              style={{
                boxShadow: '0 2px 10px rgba(0,0,0,0.04)',
                borderTop: '3px solid #faad14',
              }}
            >
              <Statistic
                title="Total Courses"
                value={stats?.curriculum?.courses ?? 0}
                valueStyle={{ color: '#faad14', fontWeight: 'bold' }}
                prefix={<ReadOutlined style={{ marginRight: 8 }} />}
                suffix={
                  <span style={{ fontSize: 12, color: '#8c8c8c', marginLeft: 8 }}>
                    ({stats?.curriculum?.prerequisite_relationships ?? 0} links)
                  </span>
                }
              />
            </Card>
          </Col>

          <Col xs={24} sm={12} lg={6}>
            <Card
              hoverable
              bordered={false}
              style={{
                boxShadow: '0 2px 10px rgba(0,0,0,0.04)',
                borderTop: '3px solid #722ed1',
              }}
            >
              <Statistic
                title="Students Enrolled"
                value={stats?.students?.total_students ?? 0}
                valueStyle={{ color: '#722ed1', fontWeight: 'bold' }}
                prefix={<UserOutlined style={{ marginRight: 8 }} />}
                suffix={
                  <span style={{ fontSize: 12, color: '#8c8c8c', marginLeft: 8 }}>
                    ({stats?.students?.active_study_plans ?? 0} plans)
                  </span>
                }
              />
            </Card>
          </Col>
        </Row>

        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          {/* AI Generation Stats Card */}
          <Col xs={24} lg={12}>
            <Card
              title={
                <Space>
                  <ApiOutlined style={{ color: '#13c2c2' }} />
                  <span>AI Generation Engine Success Rate</span>
                </Space>
              }
              bordered={false}
              style={{ boxShadow: '0 2px 10px rgba(0,0,0,0.04)', height: '100%' }}
            >
              <Row gutter={16} align="middle">
                <Col span={10} style={{ textAlign: 'center' }}>
                  <Progress
                    type="dashboard"
                    percent={stats?.ai_generations?.success_rate_pct ?? 0}
                    strokeColor={{
                      '0%': '#108ee9',
                      '100%': '#87d068',
                    }}
                    width={120}
                  />
                </Col>
                <Col span={14}>
                  <Space direction="vertical" size={8} style={{ width: '100%' }}>
                    <div>
                      <Text type="secondary">Total Configurations Handled: </Text>
                      <Text strong>{stats?.ai_generations?.total_generations ?? 0}</Text>
                    </div>
                    <div>
                      <Text type="secondary">Successful Runs: </Text>
                      <Text strong style={{ color: '#52c41a' }}>
                        {stats?.ai_generations?.successful_generations ?? 0}
                      </Text>
                    </div>
                    <div>
                      <Text type="secondary">Failed Attempts: </Text>
                      <Text strong style={{ color: '#f5222d' }}>
                        {stats?.ai_generations?.failed_generations ?? 0}
                      </Text>
                    </div>
                    <div>
                      <Text type="secondary">Avg Execution Time: </Text>
                      <Text strong>
                        {stats?.ai_generations?.avg_duration_seconds !== null && stats?.ai_generations?.avg_duration_seconds !== undefined
                          ? `${stats.ai_generations.avg_duration_seconds}s`
                          : 'N/A'}
                      </Text>
                    </div>
                  </Space>
                </Col>
              </Row>
            </Card>
          </Col>

          {/* Bulk Import History Card */}
          <Col xs={24} lg={12}>
            <Card
              title={
                <Space>
                  <ImportOutlined style={{ color: '#eb2f96' }} />
                  <span>Bulk Imports Registry</span>
                </Space>
              }
              bordered={false}
              style={{ boxShadow: '0 2px 10px rgba(0,0,0,0.04)', height: '100%' }}
            >
              <Row gutter={16} align="middle" style={{ minHeight: 120 }}>
                <Col span={12}>
                  <Statistic
                    title="Executed Sheets"
                    value={stats?.imports?.total_imports ?? 0}
                    valueStyle={{ color: '#eb2f96', fontWeight: 'bold' }}
                    suffix="Uploads"
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title="Entities Registered"
                    value={stats?.imports?.total_entities_imported ?? 0}
                    valueStyle={{ color: '#13c2c2', fontWeight: 'bold' }}
                    suffix="Objects"
                  />
                </Col>
              </Row>
              <div style={{ marginTop: 16, paddingTop: 16, borderTop: '1px solid #f0f0f0' }}>
                <Space size={6}>
                  <HistoryOutlined style={{ color: '#8c8c8c' }} />
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    Admin Operations (Last 30 days):{' '}
                    <Text strong>{stats?.recent_admin_actions_30d ?? 0}</Text> operations
                  </Text>
                </Space>
              </div>
            </Card>
          </Col>
        </Row>
      </Spin>

      {/* System Health Indicators Panel */}
      <Card
        title={
          <Space>
            <DatabaseOutlined style={{ color: '#722ed1' }} />
            <span>Infrastructure Health Status</span>
          </Space>
        }
        extra={
          health && (
            <Tag color={overallHealthProps.tagColor} icon={overallHealthProps.icon}>
              System {health.status.toUpperCase()}
            </Tag>
          )
        }
        bordered={false}
        style={{
          boxShadow: '0 2px 10px rgba(0,0,0,0.04)',
          marginBottom: 24,
          border: '1px solid #f0f0f0',
        }}
        bodyStyle={{ padding: '20px 24px' }}
      >
        <Spin spinning={isHealthLoading}>
          <Row gutter={[24, 24]}>
            {/* Database Health Card */}
            <Col xs={24} md={8}>
              <div style={{ padding: 16, background: '#f9f9f9', borderRadius: 8, height: '100%' }}>
                <Space style={{ marginBottom: 12 }}>
                  <DatabaseOutlined style={{ fontSize: 18, color: '#1890ff' }} />
                  <Text strong>Database Server</Text>
                </Space>
                <div>
                  <Space align="start">
                    {dbCheck ? (
                      getHealthStatusProps(dbCheck.status).icon
                    ) : (
                      <QuestionCircleOutlined />
                    )}
                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                      <Text style={{ fontSize: 13 }}>
                        {dbCheck ? dbCheck.message : 'Loading probe...'}
                      </Text>
                      <Text type="secondary" style={{ fontSize: 11 }}>
                        Status: {dbCheck?.status?.toUpperCase() ?? 'UNKNOWN'}
                      </Text>
                    </div>
                  </Space>
                </div>
              </div>
            </Col>

            {/* Storage Health Card */}
            <Col xs={24} md={8}>
              <div style={{ padding: 16, background: '#f9f9f9', borderRadius: 8, height: '100%' }}>
                <Space style={{ marginBottom: 12 }}>
                  <HddOutlined style={{ fontSize: 18, color: '#52c41a' }} />
                  <Text strong>Shared Storage Space</Text>
                </Space>
                <div>
                  <Space align="start" style={{ width: '100%', marginBottom: 8 }}>
                    {diskCheck ? (
                      getHealthStatusProps(diskCheck.status).icon
                    ) : (
                      <QuestionCircleOutlined />
                    )}
                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                      <Text style={{ fontSize: 13 }}>
                        {diskCheck ? diskCheck.message : 'Loading probe...'}
                      </Text>
                      <Text type="secondary" style={{ fontSize: 11 }}>
                        {diskCheck?.value || 'checking...'}
                      </Text>
                    </div>
                  </Space>
                  {diskCheck && (
                    <Progress
                      percent={getDiskUsagePercent(diskCheck)}
                      size="small"
                      status={diskCheck.status === 'error' ? 'exception' : 'active'}
                      strokeColor={diskCheck.status === 'warning' ? '#faad14' : undefined}
                    />
                  )}
                </div>
              </div>
            </Col>

            {/* RAM Health Card */}
            <Col xs={24} md={8}>
              <div style={{ padding: 16, background: '#f9f9f9', borderRadius: 8, height: '100%' }}>
                <Space style={{ marginBottom: 12 }}>
                  <ApiOutlined style={{ fontSize: 18, color: '#722ed1' }} />
                  <Text strong>Memory (RAM)</Text>
                </Space>
                <div>
                  <Space align="start" style={{ width: '100%', marginBottom: 8 }}>
                    {memCheck ? (
                      getHealthStatusProps(memCheck.status).icon
                    ) : (
                      <QuestionCircleOutlined />
                    )}
                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                      <Text style={{ fontSize: 13 }}>
                        {memCheck ? memCheck.message : 'Loading probe...'}
                      </Text>
                      <Text type="secondary" style={{ fontSize: 11 }}>
                        {memCheck?.value || 'checking...'}
                      </Text>
                    </div>
                  </Space>
                  {memCheck && getMemoryUsagePercent(memCheck) > 0 && (
                    <Progress
                      percent={getMemoryUsagePercent(memCheck)}
                      size="small"
                      status={memCheck.status === 'error' ? 'exception' : 'active'}
                      strokeColor={memCheck.status === 'warning' ? '#faad14' : undefined}
                    />
                  )}
                </div>
              </div>
            </Col>
          </Row>
        </Spin>
      </Card>

      {/* Recent Activities Feed Table */}
      <Card
        title={
          <Space>
            <HistoryOutlined style={{ color: '#1890ff' }} />
            <span>Recent Administrative Activities</span>
          </Space>
        }
        bordered={false}
        style={{
          boxShadow: '0 2px 10px rgba(0,0,0,0.04)',
          border: '1px solid #f0f0f0',
        }}
      >
        <Table
          scroll={{ x: 'max-content' }}
          columns={activityColumns}
          dataSource={activitiesData?.activities || []}
          rowKey="id"
          loading={isActivitiesLoading}
          pagination={{
            current: page,
            pageSize: pageSize,
            total: activitiesData?.total || 0,
            showSizeChanger: true,
            pageSizeOptions: ['5', '10', '20', '50'],
            onChange: (p, ps) => {
              setPage(p);
              setPageSize(ps);
            },
          }}
          locale={{
            emptyText: 'No administrative activity logs recorded.',
          }}
          style={{ fontSize: 13 }}
        />
      </Card>
    </div>
  );
};

export default AdminDashboard;
