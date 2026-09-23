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

async function downloadReport(endpoint, formData, outputName) {
  const response = await fetch(endpoint, {
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
  downloadLink.download = outputName

  document.body.appendChild(downloadLink)
  downloadLink.click()
  downloadLink.remove()

  setTimeout(() => {
    URL.revokeObjectURL(downloadUrl)
  }, 1000)
}

function App() {
  const [backendStatus, setBackendStatus] = useState('checking')

  const [profitFile, setProfitFile] = useState(null)
  const [profitProcessing, setProfitProcessing] = useState(false)
  const [profitResult, setProfitResult] = useState(null)

  const [summaryFile, setSummaryFile] = useState(null)
  const [ckFile, setCkFile] = useState(null)
  const [summaryProcessing, setSummaryProcessing] = useState(false)
  const [summaryResult, setSummaryResult] = useState(null)

  useEffect(() => {
    async function checkBackend() {
      try {
        const response = await fetch('/api/health')

        if (!response.ok) {
          throw new Error('Backend returned an error')
        }

        const data = await response.json()

        setBackendStatus(
          data.status === 'ok' ? 'connected' : 'error',
        )
      } catch {
        setBackendStatus('error')
      }
    }

    checkBackend()
  }, [])

  async function handleProfitProcess() {
    if (!profitFile) {
      return
    }

    setProfitProcessing(true)
    setProfitResult(null)

    try {
      const formData = new FormData()
      formData.append('file', profitFile)

      await downloadReport(
        '/api/profit',
        formData,
        '明细利润_处理结果.xlsx',
      )

      setProfitResult({
        type: 'success',
        message: '处理完成，明细利润文件已经下载。',
      })
    } catch (error) {
      setProfitResult({
        type: 'error',
        message:
          error instanceof Error ? error.message : '文件处理失败。',
      })
    } finally {
      setProfitProcessing(false)
    }
  }

  async function handleSummaryProcess() {
    if (!summaryFile) {
      return
    }

    setSummaryProcessing(true)
    setSummaryResult(null)

    try {
      const formData = new FormData()
      formData.append('file', summaryFile)

      if (ckFile) {
        formData.append('ck_file', ckFile)
      }

      await downloadReport(
        '/api/summary',
        formData,
        '客户总表_处理结果.xlsx',
      )

      setSummaryResult({
        type: 'success',
        message: '处理完成，客户总表已经下载。',
      })
    } catch (error) {
      setSummaryResult({
        type: 'error',
        message:
          error instanceof Error ? error.message : '文件处理失败。',
      })
    } finally {
      setSummaryProcessing(false)
    }
  }

  const currentStatus = statusDetails[backendStatus]
  const backendConnected = backendStatus === 'connected'

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
          <Col xs={24} md={12}>
            <Card title="明细利润" className="tool-card">
              <Paragraph>
                上传年度明细文件，计算每单毛利润和毛利率。
              </Paragraph>

              <Upload
                accept=".xlsx"
                maxCount={1}
                fileList={profitFile ? [profitFile] : []}
                beforeUpload={(file) => {
                  setProfitFile(file)
                  setProfitResult(null)

                  return false
                }}
                onRemove={() => {
                  setProfitFile(null)
                  setProfitResult(null)
                }}
              >
                <Button block>选择年度明细文件</Button>
              </Upload>

              {profitResult && (
                <Alert
                  type={profitResult.type}
                  message={profitResult.message}
                  showIcon
                />
              )}

              <Button
                type="primary"
                block
                loading={profitProcessing}
                disabled={!profitFile || !backendConnected}
                onClick={handleProfitProcess}
              >
                生成明细利润
              </Button>
            </Card>
          </Col>

          <Col xs={24} md={12}>
            <Card title="生成总表" className="tool-card">
              <Paragraph>
                上传已经计算过利润的明细文件，生成总体数据和客户分表。
              </Paragraph>

              <Upload
                accept=".xlsx"
                maxCount={1}
                fileList={summaryFile ? [summaryFile] : []}
                beforeUpload={(file) => {
                  setSummaryFile(file)
                  setSummaryResult(null)

                  return false
                }}
                onRemove={() => {
                  setSummaryFile(null)
                  setSummaryResult(null)
                }}
              >
                <Button block>选择明细利润文件</Button>
              </Upload>

              <Upload
                accept=".xlsx"
                maxCount={1}
                fileList={ckFile ? [ckFile] : []}
                beforeUpload={(file) => {
                  setCkFile(file)
                  setSummaryResult(null)

                  return false
                }}
                onRemove={() => {
                  setCkFile(null)
                  setSummaryResult(null)
                }}
              >
                <Button block>选择 C/K 标记文件（可选）</Button>
              </Upload>

              {summaryResult && (
                <Alert
                  type={summaryResult.type}
                  message={summaryResult.message}
                  showIcon
                />
              )}

              <Button
                type="primary"
                block
                loading={summaryProcessing}
                disabled={!summaryFile || !backendConnected}
                onClick={handleSummaryProcess}
              >
                生成客户总表
              </Button>
            </Card>
          </Col>
        </Row>
      </div>
    </main>
  )
}

export default App