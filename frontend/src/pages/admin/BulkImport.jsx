import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import apiClient from '../../api/client';
import {
  Steps,
  Button,
  Upload,
  Table,
  Collapse,
  Alert,
  Result,
  Card,
  Typography,
  Breadcrumb,
  Space,
  Spin,
  Divider,
  Row,
  Col,
  List,
  Tag,
  message,
  Modal,
} from 'antd';
import {
  InboxOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  HistoryOutlined,
  PlayCircleOutlined,
  ArrowRightOutlined,
  ArrowLeftOutlined,
  BookOutlined,
  DeleteOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons';
import { useAuth } from '../../context/AuthContext';

const { Title, Paragraph, Text } = Typography;
const { Dragger } = Upload;
const { Panel } = Collapse;
const { confirm } = Modal;

const BulkImport = () => {
  const navigate = useNavigate();
  const { hasRole } = useAuth();
  const isSuperAdmin = hasRole('super_admin');

  // Steps state
  const [currentStep, setCurrentStep] = useState(0);
  const [importSessionId, setImportSessionId] = useState(null);
  const [uploadedDetails, setUploadedDetails] = useState(null);

  // Validation step states
  const [validationData, setValidationData] = useState(null);
  const [isLoadingValidation, setIsLoadingValidation] = useState(false);

  // Preview step states
  const [previewData, setPreviewData] = useState(null);
  const [isLoadingPreview, setIsLoadingPreview] = useState(false);

  // Execution states
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState(null);

  // Reset states
  const [isResetting, setIsResetting] = useState(false);

  // Run validation when moving to step 1
  useEffect(() => {
    if (currentStep === 1 && importSessionId) {
      runValidation();
    }
  }, [currentStep]);

  // Run preview when moving to step 2
  useEffect(() => {
    if (currentStep === 2 && importSessionId) {
      runPreview();
    }
  }, [currentStep]);

  // RBAC Guard - only Super Admin can import
  if (!isSuperAdmin) {
    return (
      <div style={{ padding: 24 }}>
        <Card style={{ borderRadius: 8, boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
          <Result
            status="403"
            title="403 Access Denied"
            subTitle="Sorry, only Super Administrators have permissions to access the bulk import system."
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

  const runValidation = async () => {
    setIsLoadingValidation(true);
    try {
      const response = await apiClient.post(
        `/api/v1/admin/imports/validate?import_session_id=${importSessionId}`
      );
      setValidationData(response.data);
    } catch (err) {
      message.error(err.response?.data?.detail || 'Failed to validate uploaded file.');
      setCurrentStep(0); // return to upload
    } finally {
      setIsLoadingValidation(false);
    }
  };

  const runPreview = async () => {
    setIsLoadingPreview(true);
    try {
      const response = await apiClient.post(
        `/api/v1/admin/imports/preview?import_session_id=${importSessionId}`
      );
      setPreviewData(response.data);
    } catch (err) {
      message.error(err.response?.data?.detail || 'Failed to generate preview data.');
      setCurrentStep(1); // return to validation
    } finally {
      setIsLoadingPreview(false);
    }
  };

  const handleCustomUpload = async (options) => {
    const { file, onSuccess, onError } = options;
    const formData = new FormData();
    formData.append('file', file);
    try {
      const response = await apiClient.post('/api/v1/admin/imports/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setImportSessionId(response.data.import_session_id);
      setUploadedDetails(response.data);
      message.success('Excel file uploaded successfully.');
      onSuccess(response.data);
      setCurrentStep(1); // advance to validation
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to upload import file.';
      message.error(errorMsg);
      onError(err);
    }
  };

  const handleExecuteImport = async () => {
    setIsExecuting(true);
    try {
      const response = await apiClient.post(
        `/api/v1/admin/imports/execute?import_session_id=${importSessionId}&skip_validation=true`
      );
      setExecutionResult(response.data);
      message.success('Bulk import executed successfully.');
      setCurrentStep(3); // advance to final step
    } catch (err) {
      message.error(err.response?.data?.detail || 'Execution of bulk import failed.');
    } finally {
      setIsExecuting(false);
    }
  };

  const handleResetAllData = () => {
    confirm({
      title: 'Reset All Curriculum Data',
      icon: <ExclamationCircleOutlined />,
      content: (
        <div>
          <Paragraph>
            <Text strong type="danger">This action will permanently delete ALL:</Text>
          </Paragraph>
          <ul>
            <li>Universities</li>
            <li>Campuses</li>
            <li>Study Programs</li>
            <li>Academic Tracks</li>
            <li>Semesters</li>
            <li>Teaching Units</li>
            <li>Courses</li>
          </ul>
          <Paragraph type="danger">
            This operation cannot be undone. Are you absolutely sure?
          </Paragraph>
        </div>
      ),
      okText: 'Yes, Reset Everything',
      okType: 'danger',
      cancelText: 'Cancel',
      async onOk() {
        setIsResetting(true);
        try {
          const response = await apiClient.post('/api/v1/admin/imports/reset?confirm=true');
          message.success(`Reset completed: ${response.data.total_deleted} entities deleted`);
          // Refresh page state
          setImportSessionId(null);
          setUploadedDetails(null);
          setValidationData(null);
          setPreviewData(null);
          setExecutionResult(null);
          setCurrentStep(0);
        } catch (err) {
          message.error(err.response?.data?.detail || 'Reset operation failed.');
        } finally {
          setIsResetting(false);
        }
      },
    });
  };

  // Dragger upload props
  const uploadProps = {
    name: 'file',
    multiple: false,
    showUploadList: false,
    customRequest: handleCustomUpload,
    beforeUpload: (file) => {
      const isXlsx = file.name.endsWith('.xlsx');
      if (!isXlsx) {
        message.error('You can only upload Excel (.xlsx) spreadsheets!');
      }
      return isXlsx;
    },
  };

  // Error columns for validation issues list
  const errorColumns = [
    {
      title: 'Sheet Name',
      dataIndex: 'sheet',
      key: 'sheet',
      width: 140,
      render: (text) => <Tag color="orange">{text}</Tag>,
    },
    {
      title: 'Row',
      dataIndex: 'row',
      key: 'row',
      width: 80,
      render: (row) => <Text strong>#{row}</Text>,
    },
    {
      title: 'Validation Issue Description',
      dataIndex: 'message',
      key: 'message',
      render: (msg) => <Text type="danger">{msg}</Text>,
    },
  ];

  // Helper sample row display table generator
  const getSampleTable = (dataList) => {
    if (!dataList || dataList.length === 0) return <Text type="secondary">No rows to display.</Text>;
    const headers = Object.keys(dataList[0]);
    const cols = headers.map((h) => ({
      title: h.toUpperCase().replace('_', ' '),
      dataIndex: h,
      key: h,
      render: (val) => (val === null || val === undefined ? '—' : String(val)),
    }));
    return (
      <Table
        dataSource={dataList.map((item, idx) => ({ ...item, key: idx }))}
        columns={cols}
        size="small"
        pagination={false}
        bordered
      />
    );
  };

  return (
    <div style={{ padding: 24, background: '#fff', borderRadius: 8, minHeight: '100%' }}>
      {/* Header breadcrumb */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16, marginBottom: 24 }}>
        <div>
          <Breadcrumb style={{ marginBottom: 8 }}>
            <Breadcrumb.Item><Link to="/admin/dashboard">Admin Platform</Link></Breadcrumb.Item>
            <Breadcrumb.Item>Bulk Import Wizard</Breadcrumb.Item>
          </Breadcrumb>
          <Title level={2} style={{ margin: 0 }}>Excel Curriculum Import</Title>
          <Paragraph style={{ margin: 0, marginTop: 4 }}>
            Bulk upload curriculum configurations, universities, campuses, programs, semesters, and courses via Excel template spreadsheets.
          </Paragraph>
        </div>

        <Space>
          <Button
            danger
            icon={<DeleteOutlined />}
            onClick={handleResetAllData}
            loading={isResetting}
          >
            Reset All Data
          </Button>
          <Button
            icon={<HistoryOutlined />}
            onClick={() => navigate('/admin/imports/history')}
          >
            View Import History
          </Button>
        </Space>
      </div>

      {/* Steps indicator */}
      <Steps
        current={currentStep}
        style={{ marginBottom: 40 }}
        items={[
          { title: 'Upload Spreadsheet' },
          { title: 'Validation Check' },
          { title: 'Preview Sample Data' },
          { title: 'Execute Import' },
        ]}
      />

      {/* STEP 0: Upload Excel file dragger */}
      {currentStep === 0 && (
        <Row gutter={[24, 24]}>
          <Col xs={24} lg={15}>
            <Dragger {...uploadProps} style={{ padding: '40px 0', background: '#fafafa', borderRadius: 8 }}>
              <p className="ant-upload-drag-icon">
                <InboxOutlined style={{ color: '#1890ff', fontSize: 48 }} />
              </p>
              <p className="ant-upload-text" style={{ fontSize: 16, fontWeight: 500 }}>
                Click or drag Excel spreadsheet to this area to upload
              </p>
              <p className="ant-upload-hint" style={{ color: '#8c8c8c' }}>
                Support for single `.xlsx` files. File size limit: 20 MB.
              </p>
            </Dragger>
          </Col>
          <Col xs={24} lg={9}>
            <Card title="Excel Format Requirements" size="small" style={{ boxShadow: '0 1px 2px rgba(0,0,0,0.02)' }}>
              <Paragraph style={{ fontSize: 13 }}>
                The import spreadsheet must contain the following sheets (tabs) in exact spelling:
              </Paragraph>
              <List
                size="small"
                dataSource={[
                  'Universities',
                  'Campuses',
                  'Programs',
                  'University_Programs',
                  'Tracks',
                  'Semesters',
                  'TeachingUnits',
                  'Courses',
                  'Prerequisites',
                ]}
                renderItem={(item) => (
                  <List.Item style={{ padding: '4px 0', fontSize: 12 }}>
                    <BookOutlined style={{ color: '#1890ff', marginRight: 8 }} />
                    <Text strong>{item}</Text>
                  </List.Item>
                )}
              />
              <Divider style={{ margin: '12px 0' }} />
              <Paragraph type="secondary" style={{ fontSize: 12, margin: 0 }}>
                Download a reference curriculum worksheet layout or export curriculum details to Excel from the Universities screen to use as a format guide.
              </Paragraph>
            </Card>
          </Col>
        </Row>
      )}

      {/* STEP 1: Validation Table checks */}
      {currentStep === 1 && (
        <Card title="Structure & Validation Diagnostics" size="small">
          <Spin spinning={isLoadingValidation}>
            {validationData && (
              <div>
                {validationData.is_valid ? (
                  <div style={{ textAlign: 'center', padding: '24px 0' }}>
                    <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 48, marginBottom: 16 }} />
                    <Title level={4}>Spreadsheet is Valid!</Title>
                    <Paragraph>
                      Vite parsed {validationData.entity_counts.courses || 0} courses and related modules with zero validation issues.
                    </Paragraph>
                    <Space style={{ marginTop: 16 }}>
                      <Button onClick={() => setCurrentStep(0)} icon={<ArrowLeftOutlined />}>Re-upload</Button>
                      <Button type="primary" onClick={() => setCurrentStep(2)}>
                        Proceed to Preview <ArrowRightOutlined />
                      </Button>
                    </Space>
                  </div>
                ) : (
                  <div>
                    <Alert
                      message={`${validationData.error_count} format validation error(s) discovered`}
                      description="You must correct the spreadsheet rows listed below and re-upload before you can execute the import."
                      type="error"
                      showIcon
                      style={{ marginBottom: 20 }}
                    />
                    <Table
                      dataSource={validationData.errors.map((item, idx) => ({ ...item, key: idx }))}
                      columns={errorColumns}
                      pagination={{ pageSize: 10 }}
                      bordered
                    />
                    <div style={{ marginTop: 20, textAlign: 'right' }}>
                      <Button onClick={() => setCurrentStep(0)} icon={<ArrowLeftOutlined />}>
                        Go Back & Re-upload
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </Spin>
        </Card>
      )}

      {/* STEP 2: Previewing sample entries */}
      {currentStep === 2 && (
        <Card title="Entities Import Preview" size="small">
          <Spin spinning={isLoadingPreview}>
            {previewData && (
              <div>
                <Alert
                  message={`Ready to import ${previewData.total_entities} total records.`}
                  description="Verify counts and click next to process transaction."
                  type="info"
                  showIcon
                  style={{ marginBottom: 20 }}
                />

                <Collapse accordion style={{ marginBottom: 24 }}>
                  <Panel
                    header={
                      <div style={{ display: 'flex', justifyContent: 'space-between', width: '95%' }}>
                        <Text strong>Universities</Text>
                        <Tag color="blue">{previewData.universities.count} records</Tag>
                      </div>
                    }
                    key="1"
                  >
                    {getSampleTable(previewData.universities.samples)}
                  </Panel>
                  <Panel
                    header={
                      <div style={{ display: 'flex', justifyContent: 'space-between', width: '95%' }}>
                        <Text strong>Campuses</Text>
                        <Tag color="blue">{previewData.campuses.count} records</Tag>
                      </div>
                    }
                    key="2"
                  >
                    {getSampleTable(previewData.campuses.samples)}
                  </Panel>
                  <Panel
                    header={
                      <div style={{ display: 'flex', justifyContent: 'space-between', width: '95%' }}>
                        <Text strong>Study Programs</Text>
                        <Tag color="blue">{previewData.programs.count} records</Tag>
                      </div>
                    }
                    key="3"
                  >
                    {getSampleTable(previewData.programs.samples)}
                  </Panel>
                  <Panel
                    header={
                      <div style={{ display: 'flex', justifyContent: 'space-between', width: '95%' }}>
                        <Text strong>Academic Tracks</Text>
                        <Tag color="blue">{previewData.tracks.count} records</Tag>
                      </div>
                    }
                    key="4"
                  >
                    {getSampleTable(previewData.tracks.samples)}
                  </Panel>
                  <Panel
                    header={
                      <div style={{ display: 'flex', justifyContent: 'space-between', width: '95%' }}>
                        <Text strong>Semesters</Text>
                        <Tag color="blue">{previewData.semesters.count} records</Tag>
                      </div>
                    }
                    key="5"
                  >
                    {getSampleTable(previewData.semesters.samples)}
                  </Panel>
                  <Panel
                    header={
                      <div style={{ display: 'flex', justifyContent: 'space-between', width: '95%' }}>
                        <Text strong>Teaching Units (UE)</Text>
                        <Tag color="blue">{previewData.teaching_units.count} records</Tag>
                      </div>
                    }
                    key="6"
                  >
                    {getSampleTable(previewData.teaching_units.samples)}
                  </Panel>
                  <Panel
                    header={
                      <div style={{ display: 'flex', justifyContent: 'space-between', width: '95%' }}>
                        <Text strong>Courses</Text>
                        <Tag color="blue">{previewData.courses.count} records</Tag>
                      </div>
                    }
                    key="7"
                  >
                    {getSampleTable(previewData.courses.samples)}
                  </Panel>
                  <Panel
                    header={
                      <div style={{ display: 'flex', justifyContent: 'space-between', width: '95%' }}>
                        <Text strong>Course Prerequisites</Text>
                        <Tag color="blue">{previewData.prerequisites.count} records</Tag>
                      </div>
                    }
                    key="8"
                  >
                    {getSampleTable(previewData.prerequisites.samples)}
                  </Panel>
                </Collapse>

                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Button onClick={() => setCurrentStep(1)} icon={<ArrowLeftOutlined />}>
                    Back to Diagnostics
                  </Button>
                  <Button type="primary" onClick={handleExecuteImport} icon={<PlayCircleOutlined />}>
                    Execute Transactional Import
                  </Button>
                </div>
              </div>
            )}
          </Spin>
        </Card>
      )}

      {/* STEP 3: Progress summary result */}
      {currentStep === 3 && (
        <Card style={{ borderRadius: 8 }}>
          {isExecuting ? (
            <div style={{ textAlign: 'center', padding: '40px 0' }}>
              <Spin size="large" />
              <Title level={4} style={{ marginTop: 20 }}>Processing Transactional Database Writes...</Title>
              <Paragraph>Please do not refresh the page. The system is committing the spreadsheet curriculum atomic block.</Paragraph>
            </div>
          ) : (
            executionResult && (
              <Result
                status="success"
                title="Curriculum Import Completed Successfully!"
                subTitle={`Import committed to the database. Successfully inserted ${executionResult.total_created} total objects.`}
                extra={[
                  <Button type="primary" key="dashboard" onClick={() => navigate('/admin/dashboard')}>
                    Go to Dashboard
                  </Button>,
                  <Button key="history" onClick={() => navigate('/admin/imports/history')}>
                    View Import History (Rollbacks)
                  </Button>,
                  <Button key="another" onClick={() => {
                    setImportSessionId(null);
                    setUploadedDetails(null);
                    setValidationData(null);
                    setPreviewData(null);
                    setExecutionResult(null);
                    setCurrentStep(0);
                  }}>
                    Import Another File
                  </Button>
                ]}
              >
                <div style={{ background: '#fafafa', padding: 24, borderRadius: 8, border: '1px solid #f0f0f0' }}>
                  <Title level={5} style={{ marginTop: 0 }}>Details of committed records:</Title>
                  <Row gutter={[16, 12]}>
                    {Object.entries(executionResult.created_counts).map(([entity, count]) => (
                      <Col span={8} key={entity}>
                        <Text type="secondary">{entity.toUpperCase()}: </Text>
                        <Text strong>{String(count)}</Text>
                      </Col>
                    ))}
                  </Row>
                  <Divider style={{ margin: '16px 0' }} />
                  <div>
                    <Text type="secondary">Import Session ID: </Text>
                    <Text code>{importSessionId}</Text>
                  </div>
                  <div style={{ marginTop: 4 }}>
                    <Text type="secondary">Rollback Transaction ID: </Text>
                    <Text code>{executionResult.import_id}</Text>
                  </div>
                </div>
              </Result>
            )
          )}
        </Card>
      )}
    </div>
  );
};

export default BulkImport;
