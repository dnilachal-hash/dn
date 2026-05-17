import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { useQuery } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { Loader2, ChevronLeft, ChevronRight, Check } from 'lucide-react'
import client from '../api/client'
import { format } from 'date-fns'

interface StudentFormData {
  // Personal
  full_name: string
  father_name: string
  mother_name: string
  guardian_name: string
  dob: string
  gender: string
  category_id: string
  mobile: string
  email: string
  address: string
  // Academic
  course_id: string
  batch_id: string
  session_id: string
  professional_year: string
  roll_number: string
  admission_number: string
  registration_number: string
  enrollment_number: string
  admission_date: string
  student_status: string
  // Other
  is_hostel: boolean
  is_transport: boolean
  scholarship_status: string
  remarks: string
}

const TABS = ['Personal', 'Academic', 'Other', 'Review']

export default function StudentForm() {
  const { id } = useParams()
  const navigate = useNavigate()
  const isEdit = Boolean(id)
  const [tab, setTab] = useState(0)
  const [saving, setSaving] = useState(false)

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    reset,
    getValues,
    formState: { errors },
  } = useForm<StudentFormData>({
    defaultValues: {
      student_status: 'ACTIVE',
      gender: 'MALE',
      scholarship_status: 'NONE',
      is_hostel: false,
      is_transport: false,
      professional_year: '1',
    },
  })

  const watchCourse = watch('course_id')

  const { data: courses } = useQuery({
    queryKey: ['courses-list'],
    queryFn: () => client.get('/courses/').then((r) => r.data),
  })
  const { data: batches } = useQuery({
    queryKey: ['batches-list', watchCourse],
    queryFn: () =>
      client
        .get('/courses/batches/', { params: watchCourse ? { course_id: watchCourse } : {} })
        .then((r) => r.data),
    enabled: true,
  })
  const { data: sessions } = useQuery({
    queryKey: ['sessions-list'],
    queryFn: () => client.get('/courses/sessions/').then((r) => r.data),
  })
  const { data: categories } = useQuery({
    queryKey: ['categories-list'],
    queryFn: () => client.get('/courses/categories/').then((r) => r.data),
  })

  // Load existing student for edit
  const { data: existing, isLoading: loadingExisting } = useQuery({
    queryKey: ['student', id],
    queryFn: () => client.get(`/students/${id}`).then((r) => r.data),
    enabled: isEdit,
  })

  useEffect(() => {
    if (existing) {
      reset({
        full_name: existing.full_name || '',
        father_name: existing.father_name || '',
        mother_name: existing.mother_name || '',
        guardian_name: existing.guardian_name || '',
        dob: existing.dob ? format(new Date(existing.dob), 'yyyy-MM-dd') : '',
        gender: existing.gender || 'MALE',
        category_id: existing.category_id?.toString() || '',
        mobile: existing.mobile || '',
        email: existing.email || '',
        address: existing.address || '',
        course_id: existing.course_id?.toString() || '',
        batch_id: existing.batch_id?.toString() || '',
        session_id: existing.session_id?.toString() || '',
        professional_year: existing.professional_year?.toString() || '1',
        roll_number: existing.roll_number || '',
        admission_number: existing.admission_number || '',
        registration_number: existing.registration_number || '',
        enrollment_number: existing.enrollment_number || '',
        admission_date: existing.admission_date
          ? format(new Date(existing.admission_date), 'yyyy-MM-dd')
          : '',
        student_status: existing.student_status || 'ACTIVE',
        is_hostel: existing.is_hostel || false,
        is_transport: existing.is_transport || false,
        scholarship_status: existing.scholarship_status || 'NONE',
        remarks: existing.remarks || '',
      })
    }
  }, [existing, reset])

  const onSubmit = async (data: StudentFormData) => {
    setSaving(true)
    try {
      const payload = {
        ...data,
        course_id: data.course_id ? Number(data.course_id) : null,
        batch_id: data.batch_id ? Number(data.batch_id) : null,
        session_id: data.session_id ? Number(data.session_id) : null,
        category_id: data.category_id ? Number(data.category_id) : null,
        professional_year: data.professional_year ? Number(data.professional_year) : null,
      }
      if (isEdit) {
        await client.put(`/students/${id}`, payload)
        toast.success('Student updated successfully!')
        navigate(`/students/${id}`)
      } else {
        const res = await client.post('/students/', payload)
        toast.success('Student created successfully!')
        navigate(`/students/${res.data.id}`)
      }
    } catch (err: any) {
      const msg =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        'Failed to save student.'
      toast.error(typeof msg === 'string' ? msg : JSON.stringify(msg))
    } finally {
      setSaving(false)
    }
  }

  const values = getValues()
  const courseList = courses?.items || courses || []
  const batchList = batches?.items || batches || []
  const sessionList = sessions?.items || sessions || []
  const categoryList = categories?.items || categories || []

  const findName = (list: any[], id: string) =>
    list.find((x: any) => x.id?.toString() === id?.toString())?.name || '-'

  if (isEdit && loadingExisting) {
    return (
      <div className="flex justify-center py-16">
        <div className="animate-spin w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full" />
      </div>
    )
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">{isEdit ? 'Edit Student' : 'Add New Student'}</h1>
          <p className="text-sm text-gray-500 mt-1">
            {isEdit ? `Editing: ${existing?.full_name}` : 'Fill in the details to register a new student'}
          </p>
        </div>
        <button onClick={() => navigate(-1)} className="btn-secondary">
          <ChevronLeft size={16} />
          Back
        </button>
      </div>

      {/* Tab headers */}
      <div className="tabs mb-0">
        {TABS.map((t, i) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(i)}
            className={`tab ${tab === i ? 'tab-active' : ''} flex items-center gap-1.5`}
          >
            <span
              className={`w-5 h-5 rounded-full text-xs flex items-center justify-center font-semibold ${
                tab > i
                  ? 'bg-emerald-500 text-white'
                  : tab === i
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-200 text-gray-600'
              }`}
            >
              {tab > i ? <Check size={10} /> : i + 1}
            </span>
            {t}
          </button>
        ))}
      </div>

      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="card rounded-tl-none">
          {/* Tab 1: Personal */}
          {tab === 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div className="md:col-span-2">
                <label className="label">Full Name *</label>
                <input
                  {...register('full_name', { required: 'Full name is required' })}
                  className={`input ${errors.full_name ? 'input-error' : ''}`}
                  placeholder="Student's full name"
                />
                {errors.full_name && <p className="text-red-500 text-xs mt-1">{errors.full_name.message}</p>}
              </div>

              <div>
                <label className="label">Father's Name</label>
                <input {...register('father_name')} className="input" placeholder="Father's name" />
              </div>
              <div>
                <label className="label">Mother's Name</label>
                <input {...register('mother_name')} className="input" placeholder="Mother's name" />
              </div>
              <div>
                <label className="label">Guardian's Name</label>
                <input {...register('guardian_name')} className="input" placeholder="Guardian's name" />
              </div>
              <div>
                <label className="label">Date of Birth</label>
                <input {...register('dob')} type="date" className="input" />
              </div>
              <div>
                <label className="label">Gender *</label>
                <select {...register('gender', { required: true })} className="input">
                  <option value="MALE">Male</option>
                  <option value="FEMALE">Female</option>
                  <option value="OTHER">Other</option>
                </select>
              </div>
              <div>
                <label className="label">Category</label>
                <select {...register('category_id')} className="input">
                  <option value="">Select Category</option>
                  {categoryList.map((c: any) => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">Mobile Number</label>
                <input
                  {...register('mobile')}
                  className="input"
                  placeholder="10-digit mobile number"
                  maxLength={15}
                />
              </div>
              <div>
                <label className="label">Email Address</label>
                <input
                  {...register('email')}
                  type="email"
                  className="input"
                  placeholder="student@example.com"
                />
              </div>
              <div className="md:col-span-2">
                <label className="label">Address</label>
                <textarea
                  {...register('address')}
                  className="input"
                  rows={3}
                  placeholder="Full address"
                />
              </div>
            </div>
          )}

          {/* Tab 2: Academic */}
          {tab === 1 && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div>
                <label className="label">Course *</label>
                <select
                  {...register('course_id', { required: 'Course is required' })}
                  className={`input ${errors.course_id ? 'input-error' : ''}`}
                  onChange={(e) => { setValue('course_id', e.target.value); setValue('batch_id', '') }}
                >
                  <option value="">Select Course</option>
                  {courseList.map((c: any) => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
                {errors.course_id && <p className="text-red-500 text-xs mt-1">{errors.course_id.message}</p>}
              </div>
              <div>
                <label className="label">Batch</label>
                <select {...register('batch_id')} className="input">
                  <option value="">Select Batch</option>
                  {batchList.map((b: any) => (
                    <option key={b.id} value={b.id}>{b.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">Academic Session</label>
                <select {...register('session_id')} className="input">
                  <option value="">Select Session</option>
                  {sessionList.map((s: any) => (
                    <option key={s.id} value={s.id}>{s.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">Professional Year</label>
                <select {...register('professional_year')} className="input">
                  {[1, 2, 3, 4, 5].map((y) => (
                    <option key={y} value={y}>Year {y}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">Roll Number</label>
                <input {...register('roll_number')} className="input" placeholder="Roll number" />
              </div>
              <div>
                <label className="label">Admission Number</label>
                <input {...register('admission_number')} className="input" placeholder="Admission number" />
              </div>
              <div>
                <label className="label">Registration Number</label>
                <input {...register('registration_number')} className="input" placeholder="University registration no" />
              </div>
              <div>
                <label className="label">Enrollment Number</label>
                <input {...register('enrollment_number')} className="input" placeholder="Enrollment number" />
              </div>
              <div>
                <label className="label">Admission Date</label>
                <input {...register('admission_date')} type="date" className="input" />
              </div>
              <div>
                <label className="label">Student Status</label>
                <select {...register('student_status')} className="input">
                  <option value="ACTIVE">Active</option>
                  <option value="INACTIVE">Inactive</option>
                  <option value="ALUMNI">Alumni</option>
                  <option value="SUSPENDED">Suspended</option>
                  <option value="DROPOUT">Dropout</option>
                </select>
              </div>
            </div>
          )}

          {/* Tab 3: Other */}
          {tab === 2 && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div className="flex items-center gap-3 p-4 border border-gray-200 rounded-lg">
                <input
                  {...register('is_hostel')}
                  type="checkbox"
                  id="is_hostel"
                  className="w-4 h-4 text-indigo-600 rounded"
                />
                <label htmlFor="is_hostel" className="text-sm font-medium text-gray-700 cursor-pointer">
                  Hostel Resident
                </label>
              </div>
              <div className="flex items-center gap-3 p-4 border border-gray-200 rounded-lg">
                <input
                  {...register('is_transport')}
                  type="checkbox"
                  id="is_transport"
                  className="w-4 h-4 text-indigo-600 rounded"
                />
                <label htmlFor="is_transport" className="text-sm font-medium text-gray-700 cursor-pointer">
                  Transport Facility
                </label>
              </div>
              <div>
                <label className="label">Scholarship Status</label>
                <select {...register('scholarship_status')} className="input">
                  <option value="NONE">None</option>
                  <option value="PARTIAL">Partial</option>
                  <option value="FULL">Full</option>
                  <option value="GOVT">Government</option>
                </select>
              </div>
              <div className="md:col-span-2">
                <label className="label">Remarks</label>
                <textarea
                  {...register('remarks')}
                  className="input"
                  rows={4}
                  placeholder="Any additional remarks or notes..."
                />
              </div>
            </div>
          )}

          {/* Tab 4: Review */}
          {tab === 3 && (
            <div className="space-y-6">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-800">
                Please review all information before saving.
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Personal */}
                <div>
                  <h3 className="font-semibold text-gray-800 mb-3 pb-2 border-b">Personal Details</h3>
                  <dl className="space-y-2 text-sm">
                    {[
                      ['Full Name', values.full_name],
                      ['Father', values.father_name],
                      ['Mother', values.mother_name],
                      ['DOB', values.dob],
                      ['Gender', values.gender],
                      ['Mobile', values.mobile],
                      ['Email', values.email],
                    ].map(([k, v]) => (
                      <div key={k} className="flex gap-2">
                        <dt className="text-gray-500 w-28 shrink-0">{k}:</dt>
                        <dd className="font-medium text-gray-800">{v || '-'}</dd>
                      </div>
                    ))}
                  </dl>
                </div>

                {/* Academic */}
                <div>
                  <h3 className="font-semibold text-gray-800 mb-3 pb-2 border-b">Academic Details</h3>
                  <dl className="space-y-2 text-sm">
                    {[
                      ['Course', findName(courseList, values.course_id)],
                      ['Batch', findName(batchList, values.batch_id)],
                      ['Session', findName(sessionList, values.session_id)],
                      ['Year', values.professional_year ? `Year ${values.professional_year}` : '-'],
                      ['Roll No', values.roll_number],
                      ['Admission No', values.admission_number],
                      ['Status', values.student_status],
                    ].map(([k, v]) => (
                      <div key={k} className="flex gap-2">
                        <dt className="text-gray-500 w-28 shrink-0">{k}:</dt>
                        <dd className="font-medium text-gray-800">{v || '-'}</dd>
                      </div>
                    ))}
                  </dl>
                </div>

                {/* Other */}
                <div>
                  <h3 className="font-semibold text-gray-800 mb-3 pb-2 border-b">Other Details</h3>
                  <dl className="space-y-2 text-sm">
                    {[
                      ['Hostel', values.is_hostel ? 'Yes' : 'No'],
                      ['Transport', values.is_transport ? 'Yes' : 'No'],
                      ['Scholarship', values.scholarship_status],
                    ].map(([k, v]) => (
                      <div key={k} className="flex gap-2">
                        <dt className="text-gray-500 w-28 shrink-0">{k}:</dt>
                        <dd className="font-medium text-gray-800">{v || '-'}</dd>
                      </div>
                    ))}
                    {values.remarks && (
                      <div className="flex gap-2">
                        <dt className="text-gray-500 w-28 shrink-0">Remarks:</dt>
                        <dd className="font-medium text-gray-800">{values.remarks}</dd>
                      </div>
                    )}
                  </dl>
                </div>
              </div>
            </div>
          )}

          {/* Navigation buttons */}
          <div className="flex justify-between mt-8 pt-6 border-t border-gray-200">
            <button
              type="button"
              onClick={() => setTab((t) => Math.max(0, t - 1))}
              disabled={tab === 0}
              className="btn-secondary"
            >
              <ChevronLeft size={16} />
              Previous
            </button>

            {tab < TABS.length - 1 ? (
              <button
                type="button"
                onClick={() => setTab((t) => Math.min(TABS.length - 1, t + 1))}
                className="btn-primary"
              >
                Next
                <ChevronRight size={16} />
              </button>
            ) : (
              <button type="submit" disabled={saving} className="btn-success">
                {saving ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    Saving…
                  </>
                ) : (
                  <>
                    <Check size={16} />
                    {isEdit ? 'Update Student' : 'Create Student'}
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </form>
    </div>
  )
}
