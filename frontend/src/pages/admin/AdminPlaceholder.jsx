import { Card, Result, Breadcrumb } from 'antd';
import { ToolOutlined } from '@ant-design/icons';
import PropTypes from 'prop-types';

const AdminPlaceholder = ({ title }) => {
  return (
    <div style={{ padding: '24px', background: '#fff', borderRadius: 8, minHeight: '100%' }}>
      <Breadcrumb style={{ marginBottom: 16 }}>
        <Breadcrumb.Item>Admin Platform</Breadcrumb.Item>
        <Breadcrumb.Item>{title}</Breadcrumb.Item>
      </Breadcrumb>
      <Card bordered={false} style={{ boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
        <Result
          icon={<ToolOutlined style={{ color: '#1890ff' }} />}
          title={`Administrative Section: ${title}`}
          subTitle={`The interface for managing ${title.toLowerCase()} is under active development.`}
        />
      </Card>
    </div>
  );
};

AdminPlaceholder.propTypes = {
  title: PropTypes.string.isRequired,
};

export default AdminPlaceholder;
