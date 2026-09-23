import { useEffect, useState } from 'react'
import {
  Alert,
  Button,
  Card,
  Col,
  Row,
  Tag,
  Typography,
  Upload,
} from 'antd'

import './App.css'
import logo from './assets/skyswallow-logo.jpg'

const { Title, Paragraph } = Typography

const tools = [
  {
    id: 'profit',
    title: '明细利润',
    description: '上传年度明细文件，计算每单毛利润和毛利率。',
  },
  {
    id: 'summary',
    title: '生成总表',
    description: '根据已经计算的明细，生成客户分表和总体汇总。',
  },
]

const statusDetails = {
  checking: {
    type: 'info',
    message: '正在检查后端连接……',
  },
  connected: {
    type: 'success',
    message: '后端已连接',
  },
  error: {
    type: 'error',
    message: '无法连接后端，请确认 Flask 正在运行。',
  },
}

function App() {
  const [backendStatus, setBackendStatus] = useState('checking')
  const [selectedFile, setSelectedFile] = useState(null)
  const [processing, setProcessing] = useState(false)
  const [processResult, setProcessResult] = useState(null)

  useEffect(() => {
    async function checkBackend() {
      try {
        const response = await fetch('/api/health')

        if (!response.ok) {
          throw new Error('Backend returned an error')
        }

        const data = await response.json()

        setBackendStatus(data.status === 'ok' ? 'connected' : 'error')
      } catch {
        setBackendStatus('error')
      }
    }

    checkBackend()
  }, [])

  async function handleProfitProcess() {
    if (!selectedFile) {
      return
    }

    setProcessing(true)
    setProcessResult(null)

    try {
      const formData = new FormData()
      formData.append('file', selectedFile)

      const response = await fetch('/api/profit', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.error || '文件处理失败。')
      }

      const resultFile = await response.blob()
      const downloadUrl = URL.createObjectURL(resultFile)

      const downloadLink = document.createElement('a')
      downloadLink.href = downloadUrl
      downloadLink.download = '明细利润_处理结果.xlsx'

      document.body.appendChild(downloadLink)
      downloadLink.click()
      downloadLink.remove()

      setTimeout(() => {
        URL.revokeObjectURL(downloadUrl)
      }, 1000)

      setProcessResult({
        type: 'success',
        message: '处理完成，结果文件已经下载。',
      })
    } catch (error) {
      setProcessResult({
        type: 'error',
        message:
          error instanceof Error ? error.message : '文件处理失败。',
      })
    } finally {
      setProcessing(false)
    }
  }

  const currentStatus = statusDetails[backendStatus]

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

          <Alert
            className="backend-status"
            type={currentStatus.type}
            message={currentStatus.message}
            showIcon
          />
        </section>

        <Row gutter={[24, 24]}>
          {tools.map((tool) => (
            <Col xs={24} md={12} key={tool.id}>
              <Card title={tool.title} className="tool-card">
                <Paragraph>{tool.description}</Paragraph>

                {tool.id === 'profit' ? (
                  <>
                    <Upload
                      accept=".xlsx"
                      maxCount={1}
                      fileList={selectedFile ? [selectedFile] : []}
                      beforeUpload={(file) => {
                        setSelectedFile(file)
                        setProcessResult(null)

                        return false
                      }}
                      onRemove={() => {
                        setSelectedFile(null)
                        setProcessResult(null)
                      }}
                    >
                      <Button block>选择 Excel 文件</Button>
                    </Upload>

                    {processResult && (
                      <Alert
                        type={processResult.type}
                        message={processResult.message}
                        showIcon
                      />
                    )}

                    <Button
                      type="primary"
                      block
                      loading={processing}
                      disabled={
                        !selectedFile ||
                        backendStatus !== 'connected'
                      }
                      onClick={handleProfitProcess}
                    >
                      生成明细利润
                    </Button>
                  </>
                ) : (
                  <>
                    <Tag>稍后开发</Tag>

                    <Button type="primary" block disabled>
                      稍后连接
                    </Button>
                  </>
                )}
              </Card>
            </Col>
          ))}
        </Row>
      </div>
    </main>
  )
}

export default App