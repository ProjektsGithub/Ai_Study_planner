import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import apiClient from '../../api/client';
import {
  Table,
  Button,
  Input,
  Card,
  Typography,
  Breadcrumb,
  Space,
  Select,
  Progress,
  Tabs,
  Row,
  Col,
  Statistic,
  Tag,
  Modal,
  Alert,
  message,
} from 'antd';
import {
  FileExcelOutlined,
  FilePdfOutlined,
  BarChartOutlined,
  ReloadOutlined,
  DownloadOutlined,
  LinkOutlined,
  CalendarOutlined,
  BookOutlined,
} from '@ant-design/icons';

const { Title, Paragraph, Text } = Typography;
const { Option } = Select;

const Reports = () => {
  const [selectedUniversityId, setSelectedUniversityId] = useState(undefined);

  // Export progress states
  const [isExporting, setIsExporting] = useState(false);
  const [exportFormat, setExportFormat] = useState(null);
  const [exportProgress, setExportProgress] = useState(0);
  const [exportDuration, setExportDuration] = useState(null);
  const [progressModalOpen, setProgressModalOpen] = useState(false);

  // Summary and Prerequisites table filter states
  const [summarySearch, setSummarySearch] = useState('');
  const [prereqSearch, setPrereqSearch] = useState('');

  // 1. Fetch universities for select filtering
  const { data: uniListData } = useQuery({
    queryKey: ['allUniversitiesList'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/admin/universities?limit=200');
      return response.data;
    },
  });

  // 2. Fetch JSON curriculum summary report
  const {
    data: summaryReport,
    isLoading: isSummaryLoading,
    refetch: refetchSummary,
  } = useQuery({
    queryKey: ['adminCurriculumSummaryReport'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/admin/exports/reports/summary');
      return response.data;
    },
  });

  // 3. Fetch JSON prerequisite chain report
  const {
    data: prereqReport,
    isLoading: isPrereqsLoading,
    refetch: refetchPrereqs,
  } = useQuery({
    queryKey: ['adminPrerequisitesReport'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/admin/exports/reports/prerequisites');
      return response.data;
    },
  });

  // Perform Curriculum Export (Excel or PDF)
  const handleExport = async (format) => {
    setIsExporting(true);
    setExportFormat(format);
    setExportProgress(10);
    setExportDuration(null);
    setProgressModalOpen(true);
    const startTime = performance.now();

    try {
      const params = {};
      if (selectedUniversityId) params.university_id = selectedUniversityId;

      setExportProgress(40);
      const url =
        format === 'excel'
          ? '/api/v1/admin/exports/curriculum/excel'
          : '/api/v1/admin/exports/curriculum/pdf';

      const response = await apiClient.get(url, {
        params,
        responseType: 'blob',
      });
      setExportProgress(85);

      const mimeTypes = {
        excel: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        pdf: 'application/pdf',
      };
      const fileExtensions = {
        excel: 'xlsx',
        pdf: 'pdf',
      };

      const blob = new Blob([response.data], { type: mimeTypes[format] });
      const dlUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = dlUrl;
      const timestamp = new Date().toISOString().slice(0, 19).replace(/[-:]/g, '').replace('T', '_');
      a.download = `curriculum_export_${timestamp}.${fileExtensions[format]}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(dlUrl);

      setExportProgress(100);
      const endTime = performance.now();
      const durationMs = Math.round(endTime - startTime);
      setExportDuration(durationMs);
      message.success(`Curriculum exported as ${format.toUpperCase()} successfully in ${durationMs} ms.`);
    } catch (err) {
      message.error(`Failed to export curriculum as ${format.toUpperCase()}.`);
      setProgressModalOpen(false);
    } finally {
      setIsExporting(false);
    }
  };

  // Filter lists based on search texts
  const filteredSummaryRows = summaryReport?.rows?.filter((row) =>
    `${row.university} ${row.program} ${row.track}`
      .toLowerCase()
      .includes(summarySearch.toLowerCase())
  ) || [];

  const filteredPrereqRows = prereqReport?.relationships?.filter((row) =>
    `${row.course_name} ${row.course_code} ${row.prerequisite_name} ${row.prerequisite_code}`
      .toLowerCase()
      .includes(prereqSearch.toLowerCase())
  ) || [];

  const summaryColumns = [
    {
      title: 'University',
      dataIndex: 'university',
      key: 'university',
      sorter: (a, b) => a.university.localeCompare(b.university),
    },
    {
      title: 'Study Program',
      dataIndex: 'program',
      key: 'program',
      sorter: (a, b) => a.program.localeCompare(b.program),
    },
    {
      title: 'Academic Track',
      dataIndex: 'track',
      key: 'track',
      sorter: (a, b) => a.track.localeCompare(b.track),
    },
    {
      title: 'Level',
      dataIndex: 'track_level',
      key: 'track_level',
      width: 110,
      render: (level) => (
        <Tag color={level === 'master' ? 'cyan' : level === 'bachelor' ? 'blue' : 'gold'}>
          {level.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: 'Min ECTS',
      dataIndex: 'total_ects_required',
      key: 'total_ects_required',
      width: 110,
      render: (ects) => <Text strong>{ects} ECTS</Text>,
    },
    {
      title: 'Semesters',
      dataIndex: 'semester_count',
      key: 'semester_count',
      width: 100,
      align: 'center',
    },
    {
      title: 'Teaching Units',
      dataIndex: 'teaching_unit_count',
      key: 'teaching_unit_count',
      width: 130,
      align: 'center',
    },
    {
      title: 'Courses',
      dataIndex: 'course_count',
      key: 'course_count',
      width: 100,
      align: 'center',
    },
  ];

  const prereqColumns = [
    {
      title: 'Target Course Code',
      dataIndex: 'course_code',
      key: 'course_code',
      width: 140,
      render: (code) => (code ? <Tag color="blue">{code}</Tag> : '—'),
    },
    {
      title: 'Target Course Name',
      dataIndex: 'course_name',
      key: 'course_name',
      sorter: (a, b) => a.course_name.localeCompare(b.course_name),
    },
    {
      title: 'Target Semester',
      dataIndex: 'semester_number',
      key: 'semester_number',
      width: 120,
      render: (num) => <Text>Semester S{num}</Text>,
    },
    {
      title: 'Prerequisite Code',
      dataIndex: 'prerequisite_code',
      key: 'prerequisite_code',
      width: 140,
      render: (code) => (code ? <Tag color="purple">{code}</Tag> : '—'),
    },
    {
      title: 'Prerequisite Name',
      dataIndex: 'prerequisite_name',
      key: 'prerequisite_name',
    },
    {
      title: 'Prereq Semester',
      dataIndex: 'prerequisite_semester_number',
      key: 'prerequisite_semester_number',
      width: 120,
      render: (num) => <Text>Semester S{num}</Text>,
    },
  ];

  return (
    <div style={{ padding: 24, background: '#fff', borderRadius: 8, minHeight: '100%' }}>
      {/* Header section */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16, marginBottom: 24 }}>
        <div>
          <Breadcrumb style={{ marginBottom: 8 }}>
            <Breadcrumb.Item><Link to="/admin/dashboard">Admin Platform</Link></Breadcrumb.Item>
            <Breadcrumb.Item>Reports & Exports</Breadcrumb.Item>
          </Breadcrumb>
          <Title level={2} style={{ margin: 0 }}>Curriculum Reporting & Exports</Title>
          <Paragraph style={{ margin: 0, marginTop: 4 }}>
            Generate analytical data grids, export consolidated curriculum structures to Excel sheets, or download formatted PDF summaries.
          </Paragraph>
        </div>
      </div>

      {/* Export operations Card */}
      <Card title="Curriculum Export Controls" style={{ marginBottom: 24, boxShadow: '0 1px 2px rgba(0,0,0,0.03)' }}>
        <Row gutter={[24, 16]} align="middle">
          <Col xs={24} md={12}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <span style={{ fontWeight: 'bold', whiteSpace: 'nowrap' }}>Limit Export to University:</span>
              <Select
                style={{ width: '100%' }}
                placeholder="All Universities (Global Export)"
                value={selectedUniversityId}
                onChange={(val) => setSelectedUniversityId(val)}
                allowClear
              >
                {uniListData?.universities?.map((uni) => (
                  <Option key={uni.id} value={uni.id}>
                    {uni.name} ({uni.country})
                  </Option>
                ))}
              </Select>
            </div>
          </Col>
          <Col xs={24} md={12} style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            <Button
              type="primary"
              icon={<FileExcelOutlined />}
              onClick={() => handleExport('excel')}
              loading={isExporting && exportFormat === 'excel'}
              style={{ background: '#52c41a', borderColor: '#52c41a' }}
            >
              Export Full Excel
            </Button>
            <Button
              type="primary"
              danger
              icon={<FilePdfOutlined />}
              onClick={() => handleExport('pdf')}
              loading={isExporting && exportFormat === 'pdf'}
            >
              Export Summary PDF
            </Button>
          </Col>
        </Row>
      </Card>

      {/* Statistics and analytics grid */}
      {summaryReport && (
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={12} md={6}>
            <Card size="small" bodyStyle={{ padding: 16 }} style={{ background: '#f9f9fa' }}>
              <Statistic
                title="Total Academic Tracks"
                value={summaryReport.total_tracks}
                prefix={<BarChartOutlined style={{ color: '#1890ff' }} />}
              />
            </Card>
          </Col>
          <Col xs={12} md={6}>
            <Card size="small" bodyStyle={{ padding: 16 }} style={{ background: '#f9f9fa' }}>
              <Statistic
                title="Total Semesters"
                value={summaryReport.rows?.reduce((acc, row) => acc + row.semester_count, 0) || 0}
                prefix={<CalendarOutlined style={{ color: '#fa8c16' }} />}
              />
            </Card>
          </Col>
          <Col xs={12} md={6}>
            <Card size="small" bodyStyle={{ padding: 16 }} style={{ background: '#f9f9fa' }}>
              <Statistic
                title="Total Teaching Units"
                value={summaryReport.rows?.reduce((acc, row) => acc + row.teaching_unit_count, 0) || 0}
                prefix={<BookOutlined style={{ color: '#722ed1' }} />}
              />
            </Card>
          </Col>
          <Col xs={12} md={6}>
            <Card size="small" bodyStyle={{ padding: 16 }} style={{ background: '#f9f9fa' }}>
              <Statistic
                title="Total Active Courses"
                value={summaryReport.rows?.reduce((acc, row) => acc + row.course_count, 0) || 0}
                prefix={<BookOutlined style={{ color: '#52c41a' }} />}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* Reports Tabs */}
      <Tabs
        defaultActiveKey="summary"
        items={[
          {
            key: 'summary',
            label: (
              <span>
                <BarChartOutlined /> Curriculum Summary Report
              </span>
            ),
            children: (
              <div>
                <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
                  <Input.Search
                    placeholder="Search program, track, or university..."
                    style={{ width: 300 }}
                    value={summarySearch}
                    onChange={(e) => setSummarySearch(e.target.value)}
                    allowClear
                  />
                  <Button icon={<ReloadOutlined />} onClick={() => refetchSummary()}>
                    Refresh Data
                  </Button>
                </Row>
                <Table
                  scroll={{ x: 'max-content' }}
                  columns={summaryColumns}
                  dataSource={filteredSummaryRows.map((r, i) => ({ ...r, key: i }))}
                  loading={isSummaryLoading}
                  pagination={{ pageSize: 10 }}
                  bordered
                />
              </div>
            ),
          },
          {
            key: 'prerequisites',
            label: (
              <span>
                <LinkOutlined /> Prerequisites Chain Registry
              </span>
            ),
            children: (
              <div>
                <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
                  <Input.Search
                    placeholder="Search course code, name, prerequisite..."
                    style={{ width: 300 }}
                    value={prereqSearch}
                    onChange={(e) => setPrereqSearch(e.target.value)}
                    allowClear
                  />
                  <Button icon={<ReloadOutlined />} onClick={() => refetchPrereqs()}>
                    Refresh Data
                  </Button>
                </Row>
                <Table
                  scroll={{ x: 'max-content' }}
                  columns={prereqColumns}
                  dataSource={filteredPrereqRows.map((r, i) => ({ ...r, key: i }))}
                  loading={isPrereqsLoading}
                  pagination={{ pageSize: 15 }}
                  bordered
                />
              </div>
            ),
          },
        ]}
      />

      {/* Export progress modal */}
      <Modal
        title="Processing Export Generation"
        open={progressModalOpen}
        onCancel={() => setProgressModalOpen(false)}
        footer={[
          <Button
            key="close"
            disabled={exportProgress < 100}
            onClick={() => setProgressModalOpen(false)}
          >
            Done
          </Button>,
        ]}
        destroyOnClose
        closable={exportProgress === 100}
        maskClosable={false}
      >
        <div style={{ padding: '24px 0', textAlign: 'center' }}>
          <Progress type="circle" percent={exportProgress} style={{ marginBottom: 20 }} />
          {exportProgress < 100 ? (
            <div>
              <Title level={4}>Compiling curriculum hierarchy tree...</Title>
              <Paragraph>Converting SQLAlchemy model relationships to structured binary blobs.</Paragraph>
            </div>
          ) : (
            <div>
              <Alert
                message="Export Completed Successfully!"
                description={
                  exportDuration
                    ? `Consolidated curriculum file prepared and downloaded in ${exportDuration} ms.`
                    : 'Download successfully initiated.'
                }
                type="success"
                showIcon
              />
            </div>
          )}
        </div>
      </Modal>
    </div>
  );
};

export default Reports;
