import request from './request'

// 学校列表
export const getSchoolList = () => request.get('/schools')

// 某学校下的店铺列表，params: { page, page_size, keyword, category, sort }
export const getSchoolShops = (schoolId, params) => request.get(`/schools/${schoolId}/shops`, { params })
