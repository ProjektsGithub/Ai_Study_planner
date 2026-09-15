import { useRouteError, useNavigate } from 'react-router-dom';
import { Button, Typography, Result, Card } from 'antd';
import { WarningOutlined, HomeOutlined, ReloadOutlined } from '@ant-design/icons';

const { Title, Paragraph, Text } = Typography;

const RouteErrorBoundary = () => {
  const error = useRouteError();
  const navigate = useNavigate();

  const errorMessage =
    error?.statusText ||
    error?.message ||
    (typeof error === 'string' ? error : 'Une erreur inattendue est survenue.');

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#0f172a',
        padding: '24px',
      }}
    >
      <Card
        style={{
          maxWidth: 600,
          width: '100%',
          borderRadius: 16,
          background: 'rgba(30, 41, 59, 0.9)',
          backdropFilter: 'blur(12px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          boxShadow: '0 20px 40px rgba(0, 0, 0, 0.4)',
        }}
      >
        <Result
          status="error"
          title={
            <Title level={3} style={{ margin: 0, color: '#f8fafc' }}>
              Une erreur est survenue
            </Title>
          }
          subTitle={
            <Paragraph style={{ color: '#94a3b8', fontSize: 14 }}>
              Une erreur inattendue s'est produite lors de l'affichage de cette page. Vous pouvez rafraîchir la page ou revenir à l'accueil.
            </Paragraph>
          }
          icon={<WarningOutlined style={{ color: '#ef4444', fontSize: 48 }} />}
          extra={[
            <Button
              type="primary"
              key="reload"
              icon={<ReloadOutlined />}
              onClick={() => window.location.reload()}
              size="large"
              style={{ background: '#7c3aed', borderColor: '#7c3aed' }}
            >
              Recharger la page
            </Button>,
            <Button
              key="dashboard"
              icon={<HomeOutlined />}
              onClick={() => navigate('/dashboard')}
              size="large"
              style={{ background: 'transparent', borderColor: 'rgba(255,255,255,0.2)', color: '#f8fafc' }}
            >
              Tableau de bord
            </Button>,
          ]}
        >
          {process.env.NODE_ENV === 'development' && error && (
            <div style={{ marginTop: 24, textAlign: 'left' }}>
              <Text strong style={{ fontSize: 13, color: '#e2e8f0' }}>
                Détails de l'erreur (Mode Développement) :
              </Text>
              <pre
                style={{
                  background: '#020617',
                  padding: 16,
                  borderRadius: 8,
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  fontSize: 12,
                  maxHeight: 200,
                  overflowY: 'auto',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-all',
                  color: '#f87171',
                  fontFamily: 'Consolas, monospace',
                  marginTop: 8,
                  marginBottom: 0,
                }}
              >
                {errorMessage}
                {error?.stack && `\n\n${error.stack}`}
              </pre>
            </div>
          )}
        </Result>
      </Card>
    </div>
  );
};

export default RouteErrorBoundary;
