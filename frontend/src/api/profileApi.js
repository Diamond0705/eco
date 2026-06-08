import { baseApi } from "./baseApi.js";
import { setCurrentUser } from "../features/auth/authSlice.js";

function authUserFromProfile(profile) {
  return {
    id: profile.id,
    username: profile.username,
    full_name: [profile.first_name, profile.last_name].filter(Boolean).join(" "),
    role: profile.role
  };
}

export const profileApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    profile: builder.query({
      query: () => "profile/",
      providesTags: ["Profile"]
    }),
    updateProfile: builder.mutation({
      query: (payload) => ({
        url: "profile/",
        method: "PATCH",
        body: payload
      }),
      async onQueryStarted(_payload, { dispatch, queryFulfilled }) {
        const { data } = await queryFulfilled;
        dispatch(setCurrentUser(authUserFromProfile(data)));
      },
      invalidatesTags: ["Profile", "Auth"]
    }),
    avatarBlob: builder.query({
      query: () => ({
        url: "profile/avatar/",
        responseHandler: (response) => (response.status === 404 ? null : response.blob()),
        validateStatus: (response) => response.status === 200 || response.status === 404
      }),
      providesTags: ["Avatar"]
    }),
    uploadAvatar: builder.mutation({
      query: (file) => {
        const body = new FormData();
        body.append("avatar", file);
        return {
          url: "profile/avatar/",
          method: "POST",
          body
        };
      },
      async onQueryStarted(_file, { dispatch, queryFulfilled }) {
        const { data } = await queryFulfilled;
        dispatch(setCurrentUser(authUserFromProfile(data)));
      },
      invalidatesTags: ["Profile", "Avatar", "Auth"]
    }),
    deleteAvatar: builder.mutation({
      query: () => ({
        url: "profile/avatar/",
        method: "DELETE"
      }),
      invalidatesTags: ["Profile", "Avatar"]
    })
  })
});

export const {
  useAvatarBlobQuery,
  useDeleteAvatarMutation,
  useProfileQuery,
  useUpdateProfileMutation,
  useUploadAvatarMutation
} = profileApi;
