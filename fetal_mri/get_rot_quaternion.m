
function [rot, t] = get_rot_quaternion(header_traj)

q0 = header_traj.user_QuaternionW;
    q1 = header_traj.user_QuaternionX;
    q2 = header_traj.user_QuaternionY;
    q3 = header_traj.user_QuaternionZ;
    rot = [2 * (q0^2 + q1^2 ) - 1,   2 * (q1*q2 - q0*q3),    2 * (q1*q3 + q0*q2);
      2 * (q1*q2 + q0*q3),     2 * (q0^2 + q2^2 ) - 1,  2 * (q2*q3 - q0*q1);
      2 * (q1*q3 - q0*q2),     2 * (q2*q3 + q0*q1),    2 * (q0^2 + q3^2) - 1];

        t = ones(3,1);
         t(1) = header_traj.user_TranslationX;
         t(2) = header_traj.user_TranslationY;
         t(3) = header_traj.user_TranslationZ;
