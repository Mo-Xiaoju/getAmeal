import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import { applyClaim } from '@/api/merchant'

/** 认领申请状态 → 按钮文案。已通过的店铺会直接出现在「我的店铺」，按钮不再出现。 */
export const claimButtonText = (status) => {
  if (status === 'pending') return '已申请，等待审核'
  if (status === 'rejected') return '重新申请认领'
  return '申请认领'
}

/** 认领申请状态 → el-tag 类型。 */
export const claimStatusType = (status) =>
  ({ pending: 'warning', approved: 'success', rejected: 'danger' }[status] || 'info')

/** 认领申请状态 → 中文文案。 */
export const claimStatusText = (status) =>
  ({ pending: '待审核', approved: '已通过', rejected: '已驳回' }[status] || status || '-')

/**
 * 店铺认领申请流程。
 *
 * 「商户中心」与「店铺详情页」两处入口共用同一套动作：弹窗收集选填理由 → 提交申请
 * → 就地更新该店的申请状态。抽成 composable 是为了两处行为（含取消、错误提示）
 * 完全一致，不必各自维护一份。
 */
export function useShopClaim() {
  // 正在提交的店铺 id，供按钮 loading
  const claimingId = ref(null)

  /**
   * 对某家店提交认领申请。
   * 用户取消弹窗返回 false；提交成功返回 true（并已把 shop.my_claim_status 置为 pending）。
   */
  const applyForClaim = async (shop) => {
    let reason
    try {
      const { value } = await ElMessageBox.prompt(
        `申请认领「${shop.name}」。可补充说明你与该店的关系，便于管理员审核（选填）。`,
        '提交认领申请',
        {
          confirmButtonText: '提交申请',
          cancelButtonText: '取消',
          inputType: 'textarea',
          inputPlaceholder: '例如：本店经营者本人 / 已获得店主授权',
        }
      )
      reason = (value || '').trim()
    } catch (e) {
      return false // 用户取消
    }

    claimingId.value = shop.id
    try {
      await applyClaim(shop.id, { reason: reason || undefined })
      ElMessage.success('认领申请已提交，等待管理员审核')
      shop.my_claim_status = 'pending' // 就地更新，避免整表重拉
      return true
    } finally {
      claimingId.value = null
    }
  }

  return { claimingId, applyForClaim }
}
