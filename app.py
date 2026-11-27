# ======================
# Sidebar - Upload Expenses
# ======================
st.sidebar.markdown("---")
st.sidebar.header("📥 Upload Expenses")

uploaded_file = st.sidebar.file_uploader(
    "Upload Expenses CSV",
    type=["csv"],
    help="Supports Simplified & Traditional Chinese. Prefer CSV UTF-8 from Excel.",
    key="upload_expenses",
)

if uploaded_file is not None:
    try:
        import_df = read_csv_chinese_safe(uploaded_file)
        import_df.columns = import_df.columns.astype(str).str.strip()
        original_cols = list(import_df.columns)
        import_df = normalize_columns(import_df)

        if "Currecny" in import_df.columns and "Currency" not in import_df.columns:
            import_df = import_df.rename(columns={"Currecny": "Currency"})

        min_required = {"Date", "Category", "Amount"}
        if not min_required.issubset(set(import_df.columns)):
            st.sidebar.error(
                "Missing required columns.\n"
                "Need at least: Date, Category, Amount\n"
                f"Found: {', '.join(original_cols)}"
            )
        else:
            defaults = {
                "User": USER,
                "Currency": "HKD",
                "Vendor": "-",
                "Description": "-",
                "Remark": "-",
                "Source": "Import"
            }
            for col, default in defaults.items():
                if col not in import_df.columns:
                    import_df[col] = default

            for col in COLUMNS:
                if col not in import_df.columns:
                    import_df[col] = defaults.get(col, "-")

            import_df = import_df[COLUMNS].copy()
            import_df["Date"] = normalize_date_column(import_df["Date"])
            import_df["Amount"] = clean_amount(import_df["Amount"])
            import_df = import_df[import_df["Amount"] > 0].copy()

            for col in ["User", "Category", "Currency", "Vendor", "Description", "Remark", "Source", "Date"]:
                import_df[col] = import_df[col].fillna(defaults.get(col, "-")).astype(str).str.strip()
                import_df.loc[import_df[col] == "", col] = defaults.get(col, "-")
                if col == "Vendor":
                    import_df.loc[import_df[col].str.lower().isin(["nan", "none", "null"]), col] = "-"

            st.sidebar.markdown(f"**Preview** ({len(import_df)} rows)")
            st.sidebar.dataframe(
                import_df[["Date", "Category", "Amount", "Currency", "Vendor"]].head(8),
                use_container_width=True,
                hide_index=True
            )

            if st.sidebar.button("Import Expenses", use_container_width=True, type="primary", key="import_exp"):
                before = len(st.session_state.expenses)
                st.session_state.expenses = pd.concat(
                    [st.session_state.expenses, import_df], ignore_index=True
                )
                st.session_state.expenses["Amount"] = clean_amount(st.session_state.expenses["Amount"])
                st.session_state.expenses["Date"] = normalize_date_column(st.session_state.expenses["Date"])
                save_data()
                st.sidebar.success(f"✅ Imported {len(st.session_state.expenses) - before} expenses!")
                st.rerun()
    except Exception as e:
        st.sidebar.error(f"Error reading file: {e}")
