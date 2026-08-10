import { useState, useEffect } from 'react';
import {
  Table,
  Card,
  Button,
  Select,
  Tag,
  Space,
  Modal,
  Form,
  Input,
  TimePicker,
  Typography,
  Row,
  Col,
  Statistic,
  message,
  Popconfirm,
  Tabs,
} from 'antd';
import {
  PlusOutlined,
  CalendarOutlined,
  BookOutlined,
  ClockCircleOutlined,
  DeleteOutlined,
  EditOutlined,
  ReloadOutlined,
  EnvironmentOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import apiClient from '../../api/client';

const { Title, Paragraph, Text } = Typography;
const { Option } = Select;

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

const ClassSchedules = () => {
  const [schedules, setSchedules] = useState([]);
  const [programs, setPrograms] = useState([]);
  const [selectedProgram, setSelectedProgram] = useState(null);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [form] = Form.useForm();

  useEffect(() => {
    fetchPrograms();
    fetchSchedules();
  }, []);

  useEffect(() => {
    fetchSchedules(selectedProgram);
  }, [selectedProgram]);

  const fetchPrograms = async () => {
    try {
      const res = await apiClient.get('/api/v1/programs');
      setPrograms(res.data || []);
    } catch {
      // Fallback
    }
  };

  const fetchSchedules = async (progId = null) => {
    setLoading(true);
    try {
      const params = progId ? { study_program_id: progId } : {};
      const res = await apiClient.get('/api/v1/admin/class-schedules', { params });
      setSchedules(res.data?.items || []);
    } catch {
      message.error('Failed to load class schedules');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenModal = (record = null) => {
    setEditingItem(record);
    if (record) {
      form.setFieldsValue({
        study_program_id: record.study_program_id,
        course_name: record.course_name,
        course_code: record.course_code,
        day_of_week: record.day_of_week,
        session_type: record.session_type || 'CM',
        room_location: record.room_location,
        times: [
          record.start_time ? dayjs(record.start_time, 'HH:mm') : null,
          record.end_time ? dayjs(record.end_time, 'HH:mm') : null,
        ],
      });
    } else {
      form.resetFields();
      if (selectedProgram) {
        form.setFieldValue('study_program_id', selectedProgram);
      }
    }
    setModalOpen(true);
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      const payload = {
        study_program_id: values.study_program_id,
        course_name: values.course_name,
        course_code: values.course_code || null,
        day_of_week: values.day_of_week,
        session_type: values.session_type || 'CM',
        room_location: values.room_location || null,
        start_time: values.times[0].format('HH:mm:ss'),
        end_time: values.times[1].format('HH:mm:ss'),
        is_mandatory: true,
      };

      if (editingItem) {
        await apiClient.put(`/api/v1/admin/class-schedules/${editingItem.id}`, payload);
        message.success('Class schedule updated successfully');
      } else {
        await apiClient.post('/api/v1/admin/class-schedules', payload);
        message.success('Class schedule added successfully');
      }

      setModalOpen(false);
      fetchSchedules(selectedProgram);
    } catch (err) {
      if (err?.response?.data?.detail) {
        message.error(err.response.data.detail);
      }
    }
  };

  const handleDelete = async (id) => {
    try {
      await apiClient.delete(`/api/v1/admin/class-schedules/${id}`);
      message.success('Class schedule entry deleted');
      fetchSchedules(selectedProgram);
    } catch {
      message.error('Failed to delete class schedule entry');
    }
  };

  // Stats calculation
  const totalSlots = schedules.length;
  const cmCount = schedules.filter((s) => s.session_type === 'CM').length;
  const tdCount = schedules.filter((s) => s.session_type === 'TD').length;
  const tpCount = schedules.filter((s) => s.session_type === 'TP').length;

  const totalMinutes = schedules.reduce((acc, curr) => {
    if (!curr.start_time || !curr.end_time) return acc;
    const [sh, sm] = curr.start_time.split(':').map(Number);
    const [eh, em] = curr.end_time.split(':').map(Number);
    return acc + (eh * 60 + em - (sh * 60 + sm));
  }, 0);
  const totalHours = (totalMinutes / 60).toFixed(1);

  const columns = [
    {
      title: 'Course Name',
      dataIndex: 'course_name',
      key: 'course_name',
      render: (text, record) => (
        <div>
          <Text strong style={{ fontSize: 14 }}>{text}</Text>
          {record.course_code && (
            <div><Tag color="default">{record.course_code}</Tag></div>
          )}
        </div>
      ),
    },
    {
      title: 'Day',
      dataIndex: 'day_of_week',
      key: 'day_of_week',
      render: (day) => <Tag color="geekblue">{day}</Tag>,
    },
    {
      title: 'Time Slot',
      key: 'time_slot',
      render: (_, record) => (
        <span>
          <ClockCircleOutlined style={{ marginRight: 6, color: '#1890ff' }} />
          {record.start_time?.slice(0, 5)} - {record.end_time?.slice(0, 5)}
        </span>
      ),
    },
    {
      title: 'Type',
      dataIndex: 'session_type',
      key: 'session_type',
      render: (type) => {
        const colors = { CM: 'purple', TD: 'blue', TP: 'green', EXAM: 'red' };
        return <Tag color={colors[type] || 'blue'}>{type || 'CM'}</Tag>;
      },
    },
    {
      title: 'Room Location',
      dataIndex: 'room_location',
      key: 'room_location',
      render: (room) =>
        room ? (
          <span>
            <EnvironmentOutlined style={{ color: '#eb2f96', marginRight: 4 }} />
            {room}
          </span>
        ) : (
          <Text type="secondary">—</Text>
        ),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => handleOpenModal(record)}
          />
          <Popconfirm
            title="Delete class schedule entry?"
            onConfirm={() => handleDelete(record.id)}
            okText="Yes"
            cancelText="No"
          >
            <Button type="text" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: 24, background: '#fff', borderRadius: 8, minHeight: '100%' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24, flexWrap: 'wrap', gap: 16 }}>
        <div>
          <Title level={2} style={{ margin: 0 }}>
            🏛️ Emplois du Temps Universitaires (Class Schedules)
          </Title>
          <Paragraph style={{ margin: 0, marginTop: 4, color: '#8c8c8c' }}>
            Consultez, ajoutez et gérez les emplois du temps de cours (CM, TD, TP) par filière.
          </Paragraph>
        </div>

        <Space>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => fetchSchedules(selectedProgram)}
          >
            Actualiser
          </Button>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => handleOpenModal()}
          >
            Ajouter un Cours
          </Button>
        </Space>
      </div>

      {/* Program Filter Bar & Stats */}
      <Card style={{ marginBottom: 24, borderRadius: 8, background: '#fafafa' }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} md={8}>
            <Text strong style={{ display: 'block', marginBottom: 6 }}>
              Filtrer par Filière / Programme :
            </Text>
            <Select
              style={{ width: '100%' }}
              placeholder="Toutes les filières"
              allowClear
              value={selectedProgram}
              onChange={(val) => setSelectedProgram(val)}
            >
              {programs.map((p) => (
                <Option key={p.id} value={p.id}>
                  {p.name} {p.code ? `(${p.code})` : ''}
                </Option>
              ))}
            </Select>
          </Col>

          <Col xs={12} sm={8} md={4}>
            <Statistic title="Total Créneaux" value={totalSlots} prefix={<BookOutlined />} />
          </Col>
          <Col xs={12} sm={8} md={4}>
            <Statistic title="Heures / Semaine" value={totalHours} suffix="h" prefix={<ClockCircleOutlined />} />
          </Col>
          <Col xs={24} sm={8} md={8}>
            <Text type="secondary" style={{ fontSize: 12 }}>Répartition par Type :</Text>
            <div style={{ marginTop: 4, display: 'flex', gap: 8 }}>
              <Tag color="purple">CM: {cmCount}</Tag>
              <Tag color="blue">TD: {tdCount}</Tag>
              <Tag color="green">TP: {tpCount}</Tag>
            </div>
          </Col>
        </Row>
      </Card>

      {/* Tabs View (Table / Weekly Grid) */}
      <Tabs
        defaultActiveKey="table"
        items={[
          {
            key: 'table',
            label: (
              <span>
                <BookOutlined /> Vue Liste ({schedules.length})
              </span>
            ),
            children: (
              <Table
                columns={columns}
                dataSource={schedules}
                rowKey="id"
                loading={loading}
                pagination={{ pageSize: 15 }}
                bordered
              />
            ),
          },
          {
            key: 'grid',
            label: (
              <span>
                <CalendarOutlined /> Vue Grille Semaine
              </span>
            ),
            children: (
              <div style={{ overflowX: 'auto', padding: '12px 0' }}>
                <Row gutter={[12, 12]} wrap={false}>
                  {DAYS.map((day) => {
                    const dayItems = schedules.filter((s) => s.day_of_week === day);
                    return (
                      <Col key={day} style={{ minWidth: 180, flex: 1 }}>
                        <Card
                          size="small"
                          title={
                            <div style={{ textAlign: 'center', fontWeight: 'bold' }}>
                              {day} ({dayItems.length})
                            </div>
                          }
                          headStyle={{ background: '#f0f5ff', color: '#1d39c4' }}
                        >
                          {dayItems.length === 0 ? (
                            <Text type="secondary" style={{ display: 'block', textAlign: 'center', py: 8 }}>
                              Aucun cours
                            </Text>
                          ) : (
                            dayItems.map((item) => (
                              <Card
                                key={item.id}
                                size="small"
                                style={{
                                  marginBottom: 8,
                                  borderColor: item.session_type === 'TP' ? '#b7eb8f' : item.session_type === 'TD' ? '#91caff' : '#d3ade8',
                                  background: item.session_type === 'TP' ? '#f6ffed' : item.session_type === 'TD' ? '#e6f4ff' : '#f9f0ff',
                                }}
                              >
                                <div style={{ fontWeight: 'bold', fontSize: 13 }}>{item.course_name}</div>
                                <div style={{ fontSize: 11, color: '#595959', marginTop: 2 }}>
                                  <ClockCircleOutlined /> {item.start_time?.slice(0, 5)} - {item.end_time?.slice(0, 5)}
                                </div>
                                <div style={{ marginTop: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                  <Tag color={item.session_type === 'TP' ? 'green' : item.session_type === 'TD' ? 'blue' : 'purple'}>
                                    {item.session_type}
                                  </Tag>
                                  {item.room_location && (
                                    <Text type="secondary" style={{ fontSize: 11 }}>
                                      📍 {item.room_location}
                                    </Text>
                                  )}
                                </div>
                              </Card>
                            ))
                          )}
                        </Card>
                      </Col>
                    );
                  })}
                </Row>
              </div>
            ),
          },
        ]}
      />

      {/* Modal Add/Edit */}
      <Modal
        title={editingItem ? 'Modifier le créneau d\'emploi du temps' : 'Ajouter un créneau d\'emploi du temps'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        destroyOnClose
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item
            name="study_program_id"
            label="Filière / Programme"
            rules={[{ required: true, message: 'La filière est requise' }]}
          >
            <Select placeholder="Sélectionnez la filière">
              {programs.map((p) => (
                <Option key={p.id} value={p.id}>{p.name}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="course_name"
            label="Nom du Cours"
            rules={[{ required: true, message: 'Le nom du cours est requis' }]}
          >
            <Input placeholder="ex: Algorithmique & Structures de Données" />
          </Form.Item>

          <Row gutter={12}>
            <Col span={12}>
              <Form.Item name="course_code" label="Code Cours">
                <Input placeholder="ex: INF101" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="session_type" label="Type de Séance" initialValue="CM">
                <Select>
                  <Option value="CM">CM (Cours Magistral)</Option>
                  <Option value="TD">TD (Travaux Dirigés)</Option>
                  <Option value="TP">TP (Travaux Pratiques)</Option>
                  <Option value="EXAM">EXAM (Examen)</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={12}>
            <Col span={12}>
              <Form.Item
                name="day_of_week"
                label="Jour de la semaine"
                rules={[{ required: true, message: 'Le jour est requis' }]}
              >
                <Select placeholder="Sélectionner le jour">
                  {DAYS.map((d) => (
                    <Option key={d} value={d}>{d}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="times"
                label="Horaire (Début - Fin)"
                rules={[{ required: true, message: 'L\'horaire est requis' }]}
              >
                <TimePicker.RangePicker format="HH:mm" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="room_location" label="Salle / Amphithéâtre">
            <Input placeholder="ex: Amphi Alan Turing / Labo Info 3" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ClassSchedules;
