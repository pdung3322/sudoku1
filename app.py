import streamlit as st
import math, random, csv, io
import numpy as np

# =================== CẤU HÌNH STREAMLIT ======================
st.set_page_config(page_title="Thuật giải Sudoku", layout="wide")

# =================== CSS GIỐNG GIAO DIỆN TKINTER =============
st.markdown("""
<style>
    body {
        background-color: #f0f4fa;
    }
    .title-main {
        text-align: center;
        font-size: 30px;
        font-weight: bold;
        color: #0b5394;
        margin-bottom: 10px;
    }
    .panel-start {
        background-color: #EAF6FF;
        padding: 25px;
        border-radius: 14px;
        width: 90%;
        margin: auto;
        margin-top: 15px;
        margin-bottom: 20px;
    }
    .note-text {
        text-align: center;
        font-size: 11px;
        color: #555;
    }
    .sudoku-cell input {
        text-align: center !important;
    }
    .sudoku-label {
        font-size: 14px;
        margin-bottom: 4px;
    }
</style>
""", unsafe_allow_html=True)

# =================== THUẬT TOÁN SUDOKU (TỪ BẢN CŨ) ===================
def valid_in_board(board, n, box_size, row, col, num):
    """Kiểm tra số num có hợp lệ đặt vào (row,col) trên board kích thước n"""
    for k in range(n):
        if board[row][k] == num:
            return False
        if board[k][col] == num:
            return False
    start_r = row - row % box_size
    start_c = col - col % box_size
    for i in range(box_size):
        for j in range(box_size):
            if board[start_r + i][start_c + j] == num:
                return False
    return True

def solve_backtrack(board, n, box_size):
    """Giải Sudoku — trả về True nếu giải được"""
    for r in range(n):
        for c in range(n):
            if board[r][c] == 0:
                for num in range(1, n + 1):
                    if valid_in_board(board, n, box_size, r, c, num):
                        board[r][c] = num
                        if solve_backtrack(board, n, box_size):
                            return True
                        board[r][c] = 0
                return False
    return True

def generate_full_board(n):
    """Tạo 1 board đã giải hoàn chỉnh ngẫu nhiên."""
    box_size = int(math.sqrt(n))
    board = [[0] * n for _ in range(n)]
    nums = list(range(1, n + 1))

    def helper(pos=0):
        if pos == n * n:
            return True
        r = pos // n
        c = pos % n
        random.shuffle(nums)
        for num in nums:
            if valid_in_board(board, n, box_size, r, c, num):
                board[r][c] = num
                if helper(pos + 1):
                    return True
                board[r][c] = 0
        return False

    ok = helper()
    if not ok:
        raise RuntimeError("Không tạo được board hoàn chỉnh — thử lại.")
    return board

def remove_cells_for_difficulty(board, difficulty):
    """Xóa ô theo mức độ (không kiểm tra duy nhất 1 nghiệm để nhanh)"""
    n = len(board)
    puzzle = [row[:] for row in board]
    total = n * n

    if n == 9:
        if difficulty == "Dễ":
            remove = 40
        elif difficulty == "Trung bình":
            remove = 50
        else:
            remove = 60
    elif n == 16:
        if difficulty == "Dễ":
            remove = int(total * 0.55)
        elif difficulty == "Trung bình":
            remove = int(total * 0.65)
        else:
            remove = int(total * 0.75)
    else:  # 25
        if difficulty == "Dễ":
            remove = int(total * 0.5)
        elif difficulty == "Trung bình":
            remove = int(total * 0.65)
        else:
            remove = int(total * 0.8)

    remove = min(remove, total - 1)
    cells = [(r, c) for r in range(n) for c in range(n)]
    random.shuffle(cells)
    removed = 0
    for (r, c) in cells:
        if removed >= remove:
            break
        puzzle[r][c] = 0
        removed += 1
    return puzzle

# =================== HÀM HỖ TRỢ ===================
def empty_board(n):
    return [[0] * n for _ in range(n)]

def init_puzzle():
    """Khởi tạo đề theo cấu hình đã chọn ở màn hình start."""
    size_text = st.session_state["size_text"]
    n = int(size_text.split("x")[0])
    box = int(math.sqrt(n))
    level = st.session_state["level"]
    source = st.session_state["source"]

    if source == "Tạo ngẫu nhiên":
        full = generate_full_board(n)
        puzzle = remove_cells_for_difficulty(full, level)
    elif source == "Tự nhập thủ công":
        puzzle = empty_board(n)
    else:  # CSV
        csv_content = st.session_state.get("csv_content", None)
        if not csv_content:
            st.session_state["error_msg"] = "Chưa có dữ liệu CSV hợp lệ."
            puzzle = empty_board(n)
        else:
            reader = csv.reader(io.StringIO(csv_content))
            rows = []
            for row in reader:
                if not any(cell.strip() for cell in row):
                    continue
                tokens = [tok.strip() for tok in row if tok.strip() != ""]
                rows.append([int(tok) for tok in tokens])
            if len(rows) != n or any(len(r) != n for r in rows):
                st.session_state["error_msg"] = f"File CSV phải là ma trận {n}x{n}."
                puzzle = empty_board(n)
            else:
                puzzle = rows

    st.session_state["grid_size"] = n
    st.session_state["box_size"] = box
    st.session_state["initial_board"] = [row[:] for row in puzzle]
    st.session_state["board"] = [row[:] for row in puzzle]
    st.session_state["need_new_puzzle"] = False

def check_current_answer(board, initial, n, box_size):
    """Kiểm tra các ô người chơi nhập (chỗ initial == 0)."""
    for r in range(n):
        for c in range(n):
            if initial[r][c] == 0 and board[r][c] != 0:
                val = board[r][c]
                if not (1 <= val <= n):
                    return False, f"Số ở ô ({r+1},{c+1}) phải trong khoảng 1..{n}"
                tmp = board[r][c]
                board[r][c] = 0
                if not valid_in_board(board, n, box_size, r, c, val):
                    board[r][c] = tmp
                    return False, f"Số {val} tại ô ({r+1},{c+1}) đang bị trùng hàng/cột/ô con."
                board[r][c] = tmp
    return True, "✓ Đáp án hiện tại hợp lệ!"

# =================== STATE BAN ĐẦU ===================
if "started" not in st.session_state:
    st.session_state.started = False
if "need_new_puzzle" not in st.session_state:
    st.session_state.need_new_puzzle = False

# =================== MÀN HÌNH START ===================
if not st.session_state.started:
    st.markdown("<div class='title-main'>Thuật giải game Sudoku</div>", unsafe_allow_html=True)

    with st.container():
        st.markdown("<div class='panel-start'>", unsafe_allow_html=True)

        col_left, col_mid, col_right = st.columns([1, 2, 1])

        with col_mid:
            size_text = st.selectbox("Chọn kích thước:", ["9x9", "16x16", "25x25"])
            level = st.selectbox("Chọn mức độ:", ["Dễ", "Trung bình", "Khó"])
            source = st.selectbox("Nguồn đề:", ["Tạo ngẫu nhiên", "Tự nhập thủ công", "Mở file CSV"])
            csv_file = None
            csv_content = None
            if source == "Mở file CSV":
                csv_file = st.file_uploader("Chọn file CSV (0 = ô trống)", type=["csv"])
                if csv_file is not None:
                    csv_content = csv_file.getvalue().decode("utf-8")

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<p class='note-text'>Ghi chú: CSV định dạng mỗi hàng một dòng, phân tách bằng dấu phẩy. 0 = ô trống.</p>", unsafe_allow_html=True)

    start_clicked = st.button("Bắt đầu", type="primary")

    if start_clicked:
        st.session_state.started = True
        st.session_state.size_text = size_text
        st.session_state.level = level
        st.session_state.source = source
        if csv_file is not None:
            st.session_state.csv_content = csv_content
        else:
            st.session_state.csv_content = None
        st.session_state.need_new_puzzle = True
        st.session_state.error_msg = ""
        st.experimental_rerun()

    st.stop()

# =================== MÀN HÌNH GIẢI SUDOKU ===================
# Khởi tạo đề nếu cần (lần đầu hoặc sau khi đổi cấu hình)
if st.session_state.need_new_puzzle:
    init_puzzle()

n = st.session_state["grid_size"]
box_size = st.session_state["box_size"]
initial_board = st.session_state["initial_board"]
board = st.session_state["board"]

st.markdown("<div class='title-main'>Thuật giải game Sudoku</div>", unsafe_allow_html=True)

# Nút quay lại màn start
top_left, top_right = st.columns([4,1])
with top_right:
    if st.button("⬅ Quay lại màn hình chọn"):
        st.session_state.started = False
        st.experimental_rerun()

# Hiển thị lỗi CSV nếu có
if st.session_state.get("error_msg"):
    st.error(st.session_state["error_msg"])

col_board, col_ctrl = st.columns([3, 1])

# ----------------- BẢNG SUDOKU -----------------
with col_board:
    st.write("")  # spacing
    for r in range(n):
        cols = st.columns(n)
        for c in range(n):
            key = f"cell_{r}_{c}"
            val = board[r][c]
            default_str = "" if val == 0 else str(val)

            disabled = initial_board[r][c] != 0
            # style block màu xen kẽ
            bg_color = "#ecf6ff" if ((r // box_size) + (c // box_size)) % 2 == 0 else "#ffffff"
            cell_html = f"""
            <div style="text-align:center;">
                <input type="text" id="{key}" name="{key}" value="{default_str}"
                       maxlength="2"
                       style="width:42px;height:42px;border-radius:6px;
                              border:1px solid #9ec5ff;
                              background-color:{bg_color};
                              text-align:center;font-size:18px;" {'readonly' if disabled else ''}>
            </div>
            """
            cols[c].markdown(cell_html, unsafe_allow_html=True)

# Sau khi render, đọc lại giá trị từ session_state của text_input là không được,
# nên ta sẽ cập nhật board từ query params không được => Web này sẽ cập nhật sau khi nhấn nút.
# Để đơn giản, ta dùng form số học riêng biệt cho nút Giải / Kiểm tra.

# ----------------- PANEL ĐIỀU KHIỂN -----------------
with col_ctrl:
    st.subheader("Chức năng")

    # Đọc dữ liệu người dùng nhập bằng input số (phiên bản đơn giản)
    st.caption("📌 Khi bấm nút bên dưới, hệ thống sẽ đọc lại toàn bộ ô (0 = ô trống).")

    # Tạo form để xử lý nút
    with st.form("actions_form"):
        action = st.selectbox("Chọn hành động:",
                              ["Giải nhanh", "Kiểm tra đáp án", "Reset về đề ban đầu"])
        submitted = st.form_submit_button("Thực hiện")

    # Khi bấm nút -> đọc lại board từ HTML bằng cách hỏi lại người dùng
    # (Đơn giản: dùng bảng số riêng thay thế - không animation)
    # Để không phức tạp, ta dùng 1 lưới number_input ẩn để sync dữ liệu.

# Lưới number_input ẩn để lấy dữ liệu chính xác (Streamlit không đọc được ô HTML)
hidden_board = []
with st.expander("Bảng nhập số (ẩn) – dùng để xử lý logic", expanded=False):
    for r in range(n):
        row_vals = []
        cols = st.columns(n)
        for c in range(n):
            key_num = f"num_{r}_{c}"
            default_val = board[r][c]
            disabled = initial_board[r][c] != 0
            val = cols[c].number_input(
                "", min_value=0, max_value=n, step=1,
                value=int(default_val),
                key=key_num,
                disabled=False  # cho phép sửa, dùng như bản chính
            )
            row_vals.append(int(val))
        hidden_board.append(row_vals)

# Xử lý hành động
if 'last_action_done' not in st.session_state:
    st.session_state.last_action_done = ""

if submitted:
    # cập nhật board từ hidden_board
    st.session_state["board"] = [row[:] for row in hidden_board]
    board = st.session_state["board"]

    if action == "Reset về đề ban đầu":
        st.session_state["board"] = [row[:] for row in initial_board]
        st.success("Đã reset về đề ban đầu.")
        st.session_state.last_action_done = "reset"

    elif action == "Kiểm tra đáp án":
        ok, msg = check_current_answer(
            [row[:] for row in board],
            initial_board,
            n,
            box_size
        )
        if ok:
            st.success(msg)
        else:
            st.error(msg)
        st.session_state.last_action_done = "check"

    elif action == "Giải nhanh":
        temp = [row[:] for row in board]
        solved = solve_backtrack(temp, n, box_size)
        if solved:
            st.session_state["board"] = [row[:] for row in temp]
            st.success("✓ Đã giải xong Sudoku!")
        else:
            st.error("Không thể giải được bài này.")
        st.session_state.last_action_done = "solve"

    st.experimental_rerun()
