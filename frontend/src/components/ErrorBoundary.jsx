import { Component } from 'react';
import PropTypes from 'prop-types';
import { Button, Typography, Result, Card } from 'antd';
import { WarningOutlined, HomeOutlined, ReloadOutlined } from '@ant-design/icons';

const { Title, Paragraph, Text } = Typography;

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({
      error,
      errorInfo
    });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: '#f0f2f5',
          padding: '24px'
        }}>
          <Card
            style={{
              maxWidth: 600,
              width: '100%',
              borderRadius: 12,
              boxShadow: '0 8px 24px rgba(0,0,0,0.08)',
              border: '1px solid #f0f0f0'
            }}
          >
            <Result
              status="error"
              title={<Title level={3} style={{ margin: 0 }}>Something Went Wrong</Title>}
              subTitle={
                <Paragraph style={{ color: '#595959', fontSize: 14 }}>
                  An unexpected application error occurred. You can reload the page or navigate back to the administration panel.
                </Paragraph>
              }
              icon={<WarningOutlined style={{ color: '#ff4d4f', fontSize: 48 }} />}
              extra={[
                <Button
                  type="primary"
                  key="reload"
                  icon={<ReloadOutlined />}
                  onClick={() => window.location.reload()}
                  size="large"
                >
                  Reload Page
                </Button>,
                <Button
                  key="dashboard"
                  icon={<HomeOutlined />}
                  onClick={() => window.location.href = '/admin'}
                  size="large"
                >
                  Return Admin Panel
                </Button>
              ]}
            >
              {process.env.NODE_ENV === 'development' && this.state.error && (
                <div style={{ marginTop: 24, textAlign: 'left' }}>
                  <Text strong style={{ fontSize: 13, color: '#262626' }}>
                    Error Specifications (Development Mode Only):
                  </Text>
                  <pre
                    style={{
                      background: '#fafafa',
                      padding: 16,
                      borderRadius: 6,
                      border: '1px solid #d9d9d9',
                      fontSize: 11,
                      maxHeight: 250,
                      overflowY: 'auto',
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-all',
                      color: '#ff4d4f',
                      fontFamily: 'SFMono-Regular, Consolas, Liberation Mono, Menlo, monospace',
                      marginTop: 8,
                      marginBottom: 0
                    }}
                  >
                    {this.state.error.toString()}
                    {this.state.errorInfo && this.state.errorInfo.componentStack}
                  </pre>
                </div>
              )}
            </Result>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

ErrorBoundary.propTypes = {
  children: PropTypes.node.isRequired
};

export default ErrorBoundary;
