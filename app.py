import streamlit as st
import pandas as pd
from datetime import date, datetime

MAX_ROOMS = 100      # Giới hạn tối đa số phòng có thể quản lý
DEFAULT_ROOMS = 20   # Số phòng mặc định khi khởi động ứng dụng

ROOM_STATUSES = ["Trống", "Đang sử dụng", "Đang dọn dẹp", "Bảo trì"]
ROOM_TYPES = ["Đơn", "Đôi", "Suite", "Gia đình", "VIP"]
STATUS_ICON = {
    "Trống": "🟢",
    "Đang sử dụng": "🔴",
    "Đang dọn dẹp": "🟡",
    "Bảo trì": "⚫",
}


# ----------------------------- KHỞI TẠO DỮ LIỆU MẶC ĐỊNH -----------------------------

def init_state():
    if "rooms" not in st.session_state:
        # Mặc định tạo sẵn DEFAULT_ROOMS phòng, đánh số bắt đầu từ 101
        st.session_state.rooms = [
            {
                "id": i + 1,
                "room_number": str(101 + i),
                "room_type": "Đơn",
                "price": 400000,
                "status": "Trống",
                "note": "",
            }
            for i in range(DEFAULT_ROOMS)
        ]
    if "bookings" not in st.session_state:
        st.session_state.bookings = []
    if "next_room_id" not in st.session_state:
        st.session_state.next_room_id = DEFAULT_ROOMS + 1
    if "next_booking_id" not in st.session_state:
        st.session_state.next_booking_id = 1


# ----------------------------- HÀM HỖ TRỢ (PHÒNG) -----------------------------

def find_room(room_id):
    for r in st.session_state.rooms:
        if r["id"] == room_id:
            return r
    return None


def room_number_exists(room_number, exclude_id=None):
    return any(
        r["room_number"] == room_number and r["id"] != exclude_id
        for r in st.session_state.rooms
    )


def add_room(room_number, room_type, price, status, note):
    if len(st.session_state.rooms) >= MAX_ROOMS:
        return False, f"Đã đạt giới hạn tối đa {MAX_ROOMS} phòng. Không thể thêm phòng mới."
    if room_number_exists(room_number):
        return False, "Số phòng này đã tồn tại."
    st.session_state.rooms.append(
        {
            "id": st.session_state.next_room_id,
            "room_number": room_number,
            "room_type": room_type,
            "price": price,
            "status": status,
            "note": note,
        }
    )
    st.session_state.next_room_id += 1
    return True, "Thêm phòng thành công."


def update_room(room_id, room_number, room_type, price, status, note):
    if room_number_exists(room_number, exclude_id=room_id):
        return False, "Số phòng này đã tồn tại."
    room = find_room(room_id)
    if room:
        room.update(
            room_number=room_number, room_type=room_type, price=price, status=status, note=note
        )
        return True, "Cập nhật phòng thành công."
    return False, "Không tìm thấy phòng."


def delete_room(room_id):
    st.session_state.rooms = [r for r in st.session_state.rooms if r["id"] != room_id]
    st.session_state.bookings = [b for b in st.session_state.bookings if b["room_id"] != room_id]


def rooms_dataframe():
    return pd.DataFrame(st.session_state.rooms)


def generate_rooms(count, start_number, room_type, price, replace=True):
    """Tự động tạo `count` phòng (tối đa MAX_ROOMS), đánh số liên tiếp từ start_number."""
    count = max(1, min(count, MAX_ROOMS))
    new_rooms = []
    next_id = st.session_state.next_room_id
    for i in range(count):
        new_rooms.append(
            {
                "id": next_id,
                "room_number": str(start_number + i),
                "room_type": room_type,
                "price": price,
                "status": "Trống",
                "note": "",
            }
        )
        next_id += 1

    if replace:
        st.session_state.rooms = new_rooms
        st.session_state.bookings = []
    else:
        existing_numbers = {r["room_number"] for r in st.session_state.rooms}
        remaining_slots = MAX_ROOMS - len(st.session_state.rooms)
        added = 0
        for r in new_rooms:
            if added >= remaining_slots:
                break
            if r["room_number"] in existing_numbers:
                continue
            st.session_state.rooms.append(r)
            added += 1

    st.session_state.next_room_id = next_id
    return count


# ----------------------------- HÀM HỖ TRỢ (ĐẶT PHÒNG) -----------------------------

def add_booking(room_id, guest_name, phone, check_in, check_out):
    st.session_state.bookings.append(
        {
            "id": st.session_state.next_booking_id,
            "room_id": room_id,
            "guest_name": guest_name,
            "phone": phone,
            "check_in": str(check_in),
            "check_out": str(check_out),
            "status": "Đang ở",
            "created_at": str(datetime.now()),
        }
    )
    st.session_state.next_booking_id += 1
    room = find_room(room_id)
    if room:
        room["status"] = "Đang sử dụng"


def checkout_booking(booking_id, room_id):
    for b in st.session_state.bookings:
        if b["id"] == booking_id:
            b["status"] = "Đã trả phòng"
    room = find_room(room_id)
    if room:
        room["status"] = "Đang dọn dẹp"


def bookings_dataframe(active_only=False):
    data = st.session_state.bookings
    if active_only:
        data = [b for b in data if b["status"] == "Đang ở"]
    if not data:
        return pd.DataFrame(
            columns=["id", "room_id", "room_number", "guest_name", "phone", "check_in", "check_out", "status"]
        )
    df = pd.DataFrame(data)
    room_map = {r["id"]: r["room_number"] for r in st.session_state.rooms}
    df["room_number"] = df["room_id"].map(room_map).fillna("(đã xóa)")
    return df.sort_values("check_in", ascending=False)


# ----------------------------- GIAO DIỆN -----------------------------

def main():
    st.set_page_config(page_title="Quản lý Khách sạn", page_icon="🏨", layout="wide")
    init_state()

    st.title("🏨 Hệ thống Quản lý Phòng Khách sạn_DR BÌNH")
    st.caption(
        f"Mặc định **{DEFAULT_ROOMS} phòng**, quản lý tối đa **{MAX_ROOMS} phòng**."
    )

    tab_dashboard, tab_setup, tab_rooms, tab_add_room, tab_booking, tab_history = st.tabs(
        [
            "📊 Tổng quan",
            "⚙️ Thiết lập số phòng",
            "🛏️ Danh sách phòng",
            "➕ Thêm/Sửa phòng",
            "📅 Đặt phòng / Trả phòng",
            "📖 Lịch sử đặt phòng",
        ]
    )

    # ---------------- TAB: TỔNG QUAN ----------------
    with tab_dashboard:
        rooms_df = rooms_dataframe()
        total = len(rooms_df)
        occupied = len(rooms_df[rooms_df["status"] == "Đang sử dụng"]) if total else 0
        empty = len(rooms_df[rooms_df["status"] == "Trống"]) if total else 0
        cleaning = len(rooms_df[rooms_df["status"] == "Đang dọn dẹp"]) if total else 0
        maintenance = len(rooms_df[rooms_df["status"] == "Bảo trì"]) if total else 0

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Tổng số phòng", f"{total}/{MAX_ROOMS}")
        c2.metric("Đang sử dụng", occupied)
        c3.metric("Phòng trống", empty)
        c4.metric("Đang dọn dẹp", cleaning)
        c5.metric("Đang bảo trì", maintenance)

        st.progress(total / MAX_ROOMS if MAX_ROOMS else 0, text=f"Đã sử dụng {total}/{MAX_ROOMS} phòng")

        st.subheader("Trạng thái các phòng")
        if total == 0:
            st.info("Chưa có phòng nào. Hãy thiết lập số phòng ở tab '⚙️ Thiết lập số phòng'.")
        else:
            cols = st.columns(6)
            for i, row in rooms_df.iterrows():
                with cols[i % 6]:
                    st.markdown(
                        f"**{STATUS_ICON.get(row['status'], '⚪')} Phòng {row['room_number']}**\n\n"
                        f"{row['room_type']}\n\n"
                        f"{row['status']}"
                    )

    # ---------------- TAB: THIẾT LẬP SỐ PHÒNG ----------------
    with tab_setup:
        st.subheader("Thiết lập số lượng phòng")
        st.caption(f"Chọn số lượng phòng muốn quản lý (từ 1 đến {MAX_ROOMS}). Hệ thống sẽ tự động tạo danh sách phòng.")

        with st.form("setup_rooms_form"):
            c1, c2 = st.columns(2)
            with c1:
                room_count = st.number_input(
                    "Số lượng phòng",
                    min_value=1,
                    max_value=MAX_ROOMS,
                    value=min(len(st.session_state.rooms) or DEFAULT_ROOMS, MAX_ROOMS),
                )
                start_number = st.number_input("Số phòng bắt đầu (VD: 101)", min_value=1, value=101, step=1)
            with c2:
                default_type = st.selectbox("Loại phòng mặc định", ROOM_TYPES)
                default_price = st.number_input("Giá mặc định (VNĐ/đêm)", min_value=0.0, value=400000.0, step=50000.0)

            mode = st.radio(
                "Chế độ tạo phòng",
                ["Tạo mới toàn bộ (xóa danh sách cũ)", "Thêm vào danh sách hiện có"],
                horizontal=False,
            )

            submitted = st.form_submit_button("⚙️ Áp dụng thiết lập")
            if submitted:
                replace = mode.startswith("Tạo mới")
                if not replace and len(st.session_state.rooms) + room_count > MAX_ROOMS:
                    st.error(
                        f"Không thể thêm {room_count} phòng vì tổng số phòng sẽ vượt quá {MAX_ROOMS}. "
                        f"Hiện có {len(st.session_state.rooms)} phòng, chỉ có thể thêm tối đa {MAX_ROOMS - len(st.session_state.rooms)} phòng."
                    )
                else:
                    created = generate_rooms(room_count, start_number, default_type, default_price, replace=replace)
                    st.success(f"Đã thiết lập {created} phòng thành công (đánh số từ {start_number}).")
                    st.rerun()

        st.info(f"Hiện tại đang quản lý **{len(st.session_state.rooms)}/{MAX_ROOMS}** phòng.")

    # ---------------- TAB: DANH SÁCH PHÒNG ----------------
    with tab_rooms:
        st.subheader("Danh sách phòng")
        rooms_df = rooms_dataframe()

        filter_status = st.selectbox("Lọc theo trạng thái", ["Tất cả"] + ROOM_STATUSES)
        display_df = rooms_df if (filter_status == "Tất cả" or rooms_df.empty) else rooms_df[rooms_df["status"] == filter_status]

        if display_df.empty:
            st.info("Không có phòng nào phù hợp.")
        else:
            st.dataframe(
                display_df[["room_number", "room_type", "price", "status", "note"]].rename(
                    columns={
                        "room_number": "Số phòng",
                        "room_type": "Loại phòng",
                        "price": "Giá (VNĐ/đêm)",
                        "status": "Trạng thái",
                        "note": "Ghi chú",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )

        st.divider()
        st.subheader("Cập nhật / Xóa phòng")
        if not rooms_df.empty:
            room_options = {f"Phòng {r['room_number']} ({r['room_type']})": r["id"] for _, r in rooms_df.iterrows()}
            selected_label = st.selectbox("Chọn phòng", list(room_options.keys()))
            selected_id = room_options[selected_label]
            room_row = find_room(selected_id)

            with st.form("edit_room_form"):
                c1, c2 = st.columns(2)
                with c1:
                    new_number = st.text_input("Số phòng", value=room_row["room_number"])
                    new_type = st.selectbox(
                        "Loại phòng", ROOM_TYPES,
                        index=ROOM_TYPES.index(room_row["room_type"]) if room_row["room_type"] in ROOM_TYPES else 0,
                    )
                with c2:
                    new_price = st.number_input("Giá/đêm (VNĐ)", min_value=0.0, value=float(room_row["price"]), step=50000.0)
                    new_status = st.selectbox("Trạng thái", ROOM_STATUSES, index=ROOM_STATUSES.index(room_row["status"]))
                new_note = st.text_area("Ghi chú", value=room_row["note"] or "")

                col_save, col_delete = st.columns(2)
                submitted = col_save.form_submit_button("💾 Lưu thay đổi", use_container_width=True)
                deleted = col_delete.form_submit_button("🗑️ Xóa phòng", use_container_width=True)

                if submitted:
                    ok, msg = update_room(selected_id, new_number.strip(), new_type, new_price, new_status, new_note)
                    st.success(msg) if ok else st.error(msg)
                    if ok:
                        st.rerun()

                if deleted:
                    delete_room(selected_id)
                    st.success("Đã xóa phòng.")
                    st.rerun()
        else:
            st.info("Chưa có phòng nào để chỉnh sửa.")

    # ---------------- TAB: THÊM PHÒNG ----------------
    with tab_add_room:
        st.subheader("Thêm phòng mới")
        st.caption(f"Đang có {len(st.session_state.rooms)}/{MAX_ROOMS} phòng.")

        if len(st.session_state.rooms) >= MAX_ROOMS:
            st.warning(f"Đã đạt giới hạn tối đa {MAX_ROOMS} phòng. Vui lòng xóa bớt phòng hoặc dùng tab '⚙️ Thiết lập số phòng' để tạo lại.")

        with st.form("add_room_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                room_number = st.text_input("Số phòng (VD: 101)")
                room_type = st.selectbox("Loại phòng", ROOM_TYPES)
            with c2:
                price = st.number_input("Giá/đêm (VNĐ)", min_value=0.0, step=50000.0, value=500000.0)
                status = st.selectbox("Trạng thái ban đầu", ROOM_STATUSES)
            note = st.text_area("Ghi chú (tùy chọn)")

            submitted = st.form_submit_button("➕ Thêm phòng", disabled=len(st.session_state.rooms) >= MAX_ROOMS)
            if submitted:
                if not room_number.strip():
                    st.error("Vui lòng nhập số phòng.")
                else:
                    ok, msg = add_room(room_number.strip(), room_type, price, status, note)
                    st.success(msg) if ok else st.error(msg)

    # ---------------- TAB: ĐẶT PHÒNG / TRẢ PHÒNG ----------------
    with tab_booking:
        st.subheader("Đặt phòng mới")
        rooms_df = rooms_dataframe()
        available_rooms = rooms_df[rooms_df["status"] == "Trống"] if not rooms_df.empty else rooms_df

        if available_rooms.empty:
            st.warning("Hiện không có phòng trống nào.")
        else:
            with st.form("booking_form", clear_on_submit=True):
                room_options = {
                    f"Phòng {r['room_number']} ({r['room_type']}) - {r['price']:,.0f}đ/đêm": r["id"]
                    for _, r in available_rooms.iterrows()
                }
                selected_label = st.selectbox("Chọn phòng", list(room_options.keys()))
                guest_name = st.text_input("Tên khách hàng")
                phone = st.text_input("Số điện thoại")
                c1, c2 = st.columns(2)
                check_in = c1.date_input("Ngày nhận phòng", value=date.today())
                check_out = c2.date_input("Ngày trả phòng", value=date.today())

                submitted = st.form_submit_button("📅 Đặt phòng")
                if submitted:
                    if not guest_name.strip():
                        st.error("Vui lòng nhập tên khách hàng.")
                    elif check_out <= check_in:
                        st.error("Ngày trả phòng phải sau ngày nhận phòng.")
                    else:
                        add_booking(room_options[selected_label], guest_name.strip(), phone.strip(), check_in, check_out)
                        st.success("Đặt phòng thành công!")
                        st.rerun()

        st.divider()
        st.subheader("Trả phòng")
        active_df = bookings_dataframe(active_only=True)
        if active_df.empty:
            st.info("Không có phòng nào đang được sử dụng.")
        else:
            for _, b in active_df.iterrows():
                with st.container(border=True):
                    c1, c2, c3 = st.columns([3, 2, 1])
                    c1.markdown(f"**Phòng {b['room_number']}** — {b['guest_name']} ({b['phone']})")
                    c2.markdown(f"Nhận: {b['check_in']} → Trả: {b['check_out']}")
                    if c3.button("✅ Trả phòng", key=f"checkout_{b['id']}"):
                        checkout_booking(b["id"], b["room_id"])
                        st.success(f"Đã trả phòng {b['room_number']}.")
                        st.rerun()

    # ---------------- TAB: LỊCH SỬ ----------------
    with tab_history:
        st.subheader("Lịch sử đặt phòng")
        history_df = bookings_dataframe()
        if history_df.empty:
            st.info("Chưa có lịch sử đặt phòng.")
        else:
            st.dataframe(
                history_df[["room_number", "guest_name", "phone", "check_in", "check_out", "status"]].rename(
                    columns={
                        "room_number": "Số phòng",
                        "guest_name": "Khách hàng",
                        "phone": "SĐT",
                        "check_in": "Nhận phòng",
                        "check_out": "Trả phòng",
                        "status": "Trạng thái",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )


if __name__ == "__main__":
    main()
