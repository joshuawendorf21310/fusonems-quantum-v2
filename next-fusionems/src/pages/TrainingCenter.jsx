import { useEffect, useState } from 'react'
import SectionHeader from '../components/SectionHeader.jsx'
import DataTable from '../components/DataTable.jsx'
import AdvisoryPanel from '../components/AdvisoryPanel.jsx'
import { apiFetch } from '../services/api.js'
import {
  fallbackTrainingCourses,
  fallbackTrainingEnrollments,
  fallbackCredentials,
  fallbackSkills,
  fallbackCE,
} from '../data/fallback.js'

const courseColumns = [
  { key: 'title', label: 'Course' },
  { key: 'category', label: 'Category' },
  { key: 'status', label: 'Status' },
  { key: 'credit_hours', label: 'CE Hours' },
]

const enrollmentColumns = [
  { key: 'course_id', label: 'Course' },
  { key: 'user_id', label: 'User' },
  { key: 'status', label: 'Status' },
  { key: 'score', label: 'Score' },
]

const credentialColumns = [
  { key: 'credential_type', label: 'Credential' },
  { key: 'issuer', label: 'Issuer' },
  { key: 'status', label: 'Status' },
]

const skillColumns = [
  { key: 'skill_name', label: 'Skill' },
  { key: 'evaluator', label: 'Evaluator' },
  { key: 'status', label: 'Status' },
]

const ceColumns = [
  { key: 'category', label: 'Category' },
  { key: 'hours', label: 'Hours' },
  { key: 'status', label: 'Status' },
]

export default function TrainingCenter() {
  const [courses, setCourses] = useState(fallbackTrainingCourses)
  const [enrollments, setEnrollments] = useState(fallbackTrainingEnrollments)
  const [credentials, setCredentials] = useState(fallbackCredentials)
  const [skills, setSkills] = useState(fallbackSkills)
  const [ceRecords, setCeRecords] = useState(fallbackCE)

  const loadTraining = async () => {
    try {
      const [courseData, enrollmentData, credentialData, skillData, ceData] = await Promise.all([
        apiFetch('/api/training-center/courses'),
        apiFetch('/api/training-center/enrollments'),
        apiFetch('/api/training-center/credentials'),
        apiFetch('/api/training-center/skills'),
        apiFetch('/api/training-center/ce'),
      ])
      if (Array.isArray(courseData) && courseData.length > 0) {
        setCourses(courseData)
      }
      if (Array.isArray(enrollmentData) && enrollmentData.length > 0) {
        setEnrollments(enrollmentData)
      }
      if (Array.isArray(credentialData) && credentialData.length > 0) {
        setCredentials(credentialData)
      }
      if (Array.isArray(skillData) && skillData.length > 0) {
        setSkills(skillData)
      }
      if (Array.isArray(ceData) && ceData.length > 0) {
        setCeRecords(ceData)
      }
    } catch (error) {
      console.warn('Training center unavailable', error)
    }
  }

  useEffect(() => {
    loadTraining()
  }, [])

  return (
    <div className="page">
      <SectionHeader
        eyebrow="Training Center"
        title="Credentialing, Skills, CE"
        action={<button className="primary-button">Assign Training</button>}
      />

      <div className="section-grid">
        <div className="panel">
          <SectionHeader eyebrow="Courses" title="Active Curriculum" />
          <DataTable columns={courseColumns} rows={courses} emptyState="No courses yet." />
        </div>
        <div className="panel">
          <AdvisoryPanel
            title="Credential Risk"
            model="credential-watch"
            version="1.5"
            level="ADVISORY"
            message="2 paramedics require renewal within 14 days. Shift lockout pending."
            reason="Credential expiration rules"
          />
          <div className="note-card">
            <p className="note-title">CE Progress</p>
            <p className="note-body">Average CE completion is 72% of annual requirement.</p>
          </div>
        </div>
      </div>

      <div className="panel">
        <SectionHeader eyebrow="Enrollments" title="Active Training" />
        <DataTable columns={enrollmentColumns} rows={enrollments} emptyState="No enrollments yet." />
      </div>

      <div className="section-grid">
        <div className="panel">
          <SectionHeader eyebrow="Credentials" title="License Registry" />
          <DataTable columns={credentialColumns} rows={credentials} emptyState="No credentials yet." />
        </div>
        <div className="panel">
          <SectionHeader eyebrow="Skills" title="Skill Checkoffs" />
          <DataTable columns={skillColumns} rows={skills} emptyState="No skills recorded." />
        </div>
      </div>

      <div className="panel">
        <SectionHeader eyebrow="Continuing Education" title="CE Tracking" />
        <DataTable columns={ceColumns} rows={ceRecords} emptyState="No CE records." />
      </div>
    </div>
  )
}
