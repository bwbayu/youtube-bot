export const DashboardPage = () => {

  const handleLogout = async () => {
  try {
    const res = await fetch("http://localhost:8000/auth/logout", {
      method: "POST",
      credentials: "include",
    })

    const data = await res.json()

    if (res.ok && data.logout_status) {
      console.info(data.message)
    } else {
      console.warn(data.message || "Logout failed.")
    }

    // Redirect to home
    window.location.href = "/"
  } catch (err) {
    console.error("Logout failed:", err)
  }
}

  return (
    <>
    {/* TODO: get user data by using cookie */}
      <div>
        <h1>dashboard</h1>
        <button
        onClick={handleLogout}
        className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded"
        >
        Logout
        </button>
      </div>
    </>
  )
}