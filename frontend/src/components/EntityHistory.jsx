import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import apiClient from '../api/client';
import {
  Timeline,
  Spin,
  Tag,
  Typography,
  Button,
  Empty,
  Card,
  Space,
} from 'antd';
import {
  ClockCircleOutlined,
  UserOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
} from '@ant-design/icons';

const { Text, Paragraph } = Typography;

const EntityHistory = ({ entityType, entityId }) => {
  const [currentPage, setCurrentPage] = useState(1);
  const [accumulatedLogs, setAccumulatedLogs] = useState([]);
  const pageSize = 10;

  // Fetch chronological entity history
  const { data, isLoading, isFetching } = useQuery({
    queryKey: ['entityHistory', entityType, entityId, currentPage],
    queryFn: async () => {
      if (!entityType || !entityId) return { history: [], total: 0 };
      const response = await apiClient.get(
        `/api/v1/admin/audit/entity/${entityType}/${entityId}`,
        {
          params: { page: currentPage, page_size: pageSize },
        }
      );
      return response.data;
    },
    keepPreviousData: true,
    enabled: !!entityType && !!entityId,
  });

  // Accumulate logs when page changes or query returns
  useEffect(() => {
    if (data?.history) {
      if (currentPage === 1) {
        setAccumulatedLogs(data.history);
      } else {
        // Avoid duplicate items if query re-runs
        setAccumulatedLogs((prev) => {
          const prevIds = new Set(prev.map((item) => item.id));
          const newItems = data.history.filter((item) => !prevIds.has(item.id));
          return [...prev, ...newItems];
        });
      }
    }
  }, [data, currentPage]);

  // Reset when entity props change
  useEffect(() => {
    setCurrentPage(1);
    setAccumulatedLogs([]);
  }, [entityType, entityId]);

  if (isLoading && currentPage === 1) {
    return (
      <div style={{ textAlign: 'center', padding: '40px 0' }}>
        <Spin size="medium" tip="Loading change history..." />
      </div>
    );
  }

  if (accumulatedLogs.length === 0) {
    return (
      <Empty
        image={Empty.PRESENTED_IMAGE_SIMPLE}
        description="No audit change history found for this record."
      />
    );
  }

  const operationConfig = {
    create: {
      color: 'green',
      icon: <PlusOutlined />,
      label: 'Created',
    },
    update: {
      color: 'blue',
      icon: <EditOutlined />,
      label: 'Updated',
    },
    delete: {
      color: 'red',
      icon: <DeleteOutlined />,
      label: 'Deleted',
    },
  };

  // Helper to generate key-by-key changes list for update logs
  const renderFieldDiffs = (before, after) => {
    if (!before || !after) return null;
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

    if (diffs.length === 0) return null;

    return (
      <Card
        size="small"
        style={{
          marginTop: 8,
          background: '#fcfcfc',
          border: '1px solid #f0f0f0',
          borderRadius: 4,
        }}
        bodyStyle={{ padding: '8px 12px' }}
      >
        <span style={{ fontSize: 11, fontWeight: '600', color: '#8c8c8c' }}>FIELD MUTATIONS:</span>
        <div style={{ marginTop: 4 }}>
          {diffs.map((diff, idx) => (
            <div key={idx} style={{ fontSize: 12, margin: '2px 0', lineHeight: 1.5 }}>
              <Text strong style={{ fontSize: 11 }}>{diff.field}: </Text>
              <Text delete type="danger" style={{ background: '#fff1f0', padding: '0 4px', borderRadius: 2 }}>
                {diff.oldVal}
              </Text>
              <Text type="secondary" style={{ margin: '0 4px' }}>&rarr;</Text>
              <Text type="success" style={{ background: '#f6ffed', padding: '0 4px', borderRadius: 2, fontWeight: 500 }}>
                {diff.newVal}
              </Text>
            </div>
          ))}
        </div>
      </Card>
    );
  };

  const hasMore = data?.total > accumulatedLogs.length;

  return (
    <div style={{ padding: '8px 4px' }}>
      <Timeline mode="left">
        {accumulatedLogs.map((log) => {
          const config = operationConfig[log.operation] || {
            color: 'gray',
            icon: <ClockCircleOutlined />,
            label: log.operation.toUpperCase(),
          };

          return (
            <Timeline.Item
              key={log.id}
              dot={config.icon}
              color={config.color}
              label={
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {new Date(log.timestamp).toLocaleString()}
                </Text>
              }
            >
              <div style={{ paddingLeft: 4 }}>
                <Space size={6} align="baseline" wrap style={{ marginBottom: 4 }}>
                  <Tag color={config.color} style={{ fontWeight: '600', fontSize: 10 }}>
                    {config.label}
                  </Tag>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    <UserOutlined style={{ fontSize: 10, marginRight: 3 }} />
                    {log.user_email || `User #${log.user_id}`}
                  </Text>
                </Space>

                <Paragraph style={{ margin: 0, fontSize: 13, fontWeight: 500 }}>
                  {log.description || 'Record audit modifications.'}
                </Paragraph>

                {log.operation === 'update' &&
                  renderFieldDiffs(log.before_value, log.after_value)}
              </div>
            </Timeline.Item>
          );
        })}
      </Timeline>

      {hasMore && (
        <div style={{ textAlign: 'center', marginTop: 16, marginBottom: 8 }}>
          <Button
            size="small"
            onClick={() => setCurrentPage((prev) => prev + 1)}
            loading={isFetching}
          >
            Load Older History
          </Button>
        </div>
      )}
    </div>
  );
};

export default EntityHistory;
