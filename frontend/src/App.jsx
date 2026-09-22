import { Button, Card, Col, Row, Tag, Typography } from 'antd'
import './App.css'
import logo from './assets/skyswallow-logo.jpg'

const { Title, Paragraph } = Typography

const tools = [
  {
    title: '明细利润',
    description: '上传年度明细文件，计算每单毛利润和毛利率。',
  },
  {
    title: '生成总表',
    description: '根据已经计算的明细，生成客户分表和总体汇总。',
  },
]

function App() {
  return (
    <main className="page">
      <div className="container">
        <section className="introduction">
            <img
  src={logo}
  alt="SkySwallow"
  className="brand-logo"
/>
          <Tag color="blue">本地内部系统</Tag>
          <Title>SkySwallow Tools</Title>
          <Paragraph type="secondary">
            选择需要使用的报表工具。
          </Paragraph>
        </section>

        <Row gutter={[24, 24]}>
          {tools.map((tool) => (
            <Col xs={24} md={12} key={tool.title}>
              <Card title={tool.title} className="tool-card">
                <Paragraph>{tool.description}</Paragraph>
                <Tag>界面原型</Tag>
                <Button type="primary" block disabled>
                  稍后连接
                </Button>
              </Card>
            </Col>
          ))}
        </Row>
      </div>
    </main>
  )
}

export default App