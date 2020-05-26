#include <map/landmark.h>
#include <map/shot.h>

#include <algorithm>

namespace map {
LandmarkUniqueId Landmark::landmark_unique_id_ = 0;

Landmark::Landmark(const LandmarkId lm_id, const Vec3d& global_pos)
    : id_(lm_id),
      unique_id_(Landmark::landmark_unique_id_),
      global_pos_(global_pos),
      color_(255, 0, 0) {
  ++Landmark::landmark_unique_id_;
}

Vec3f Landmark::GetObservationInShot(Shot* shot) const {
  const auto it = observations_.find(shot);
  if (it == observations_.end()) {
    throw std::runtime_error("No observation in shot " + shot->id_);
  }
  return shot->GetKeyPointEigen(it->second);
}

void Landmark::SetReprojectionErrors(
    const std::unordered_map<std::string, Eigen::VectorXd> reproj_errors) {
  reproj_errors_ = reproj_errors;
}

double Landmark::ComputeDistanceFromRefFrame() const {
  const Vec3d cam_to_lm_vec =
      global_pos_ - ref_shot_->GetPose().GetOrigin();
  return cam_to_lm_vec.norm();
}

};  // namespace map