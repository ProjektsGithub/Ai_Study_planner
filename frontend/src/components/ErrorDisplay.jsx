import { Alert, Typography, Collapse, Button } from 'antd';
import { WarningOutlined, ReloadOutlined } from '@ant-design/icons';
import PropTypes from 'prop-types';

const { Text, Paragraph } = Typography;
const { Panel } = Collapse;

const ErrorDisplay = ({ title, error, message, onRetry }) => {
  // Extract clean error message from Axios / backend response
  let detailedMessage = message || '';
  let errorDetails = '';

  if (error) {
    if (error.response?.data?.detail) {
      if (typeof error.response.data.detail === 'string') {
        detailedMessage = error.response.data.detail;
      } else if (Array.isArray(error.response.data.detail)) {
        detailedMessage = error.response.data.detail
          .map((d) => `[${d.loc?.join('.') || 'field'}]: ${d.msg}`)
          .join('\n');
      } else {
        detailedMessage = JSON.stringify(error.response.data.detail);
      }
    } else if (error.message) {
      detailedMessage = error.message;
    }

    // Capture stack trace or request info if available
    if (error.config) {
      errorDetails += `Request URL: ${error.config.method?.toUpperCase()} ${error.config.url}\n`;
    }
    if (error.response) {
      errorDetails += `Status: ${error.response.status} ${error.response.statusText}\n`;
      errorDetails += `Response Data: ${JSON.stringify(error.response.data, null, 2)}`;
    } else if (error.stack) {
      errorDetails += error.stack;
    }
  }

  const errorTitle = title || 'An operation error occurred';

  const description = (
    <div style={{ marginTop: '8px' }}>
      <Paragraph style={{ margin: 0, fontSize: '13px', color: '#595959' }}>
        {detailedMessage || 'Please verify system parameters, check your connectivity, or contact an administrator.'}
      </Paragraph>
      
      {errorDetails && (
        <Collapse ghost style={{ marginTop: '12px' }}>
          <Panel
            header={
              <Text type="secondary" style={{ fontSize: '12px', cursor: 'pointer' }}>
                Technical Details & Diagnostics
              </Text>
            }
            key="diagnostics"
          >
            <pre
              style={{
                background: '#f5f5f5',
                padding: '12px',
                borderRadius: '4px',
                border: '1px solid #d9d9d9',
                fontSize: '11px',
                maxHeight: '180px',
                overflowY: 'auto',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-all',
                color: '#ff4d4f',
                fontFamily: 'SFMono-Regular, Consolas, Liberation Mono, Menlo, monospace',
                margin: 0,
              }}
            >
              {errorDetails}
            </pre>
          </Panel>
        </Collapse>
      )}

      {onRetry && (
        <div style={{ marginTop: '16px' }}>
          <Button
            type="primary"
            danger
            size="small"
            icon={<ReloadOutlined />}
            onClick={onRetry}
          >
            Retry Operation
          </Button>
        </div>
      )}
    </div>
  );

  return (
    <Alert
      message={
        <Text strong style={{ fontSize: '15px', color: '#a8071a' }}>
          {errorTitle}
        </Text>
      }
      description={description}
      type="error"
      showIcon
      icon={<WarningOutlined style={{ color: '#cf1322', fontSize: '20px' }} />}
      style={{
        borderRadius: '8px',
        border: '1px solid #ffa39e',
        background: '#fff1f0',
        boxShadow: '0 2px 8px rgba(255, 77, 79, 0.08)',
        marginBottom: '20px',
        padding: '16px 24px',
      }}
    />
  );
};

ErrorDisplay.propTypes = {
  title: PropTypes.string,
  error: PropTypes.object,
  message: PropTypes.string,
  onRetry: PropTypes.func,
};

export default ErrorDisplay;
