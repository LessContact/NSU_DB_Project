# --- FILTER CONFIGURATION ---
# This dictionary maps a view/function name to its available filters.
# The format for each filter is as follows:
# 'filter_key': ('table_name', 'display_name_column', 'id_column') -> Fetches from DB
# 'filter_key': ['Option1', 'Option2'] -> A hardcoded list of options
# 'filter_key': 'boolean' -> A True/False choice
# 'filter_key': 'date' -> Indicates a date input is required

FILTER_CONFIG = {
    'v_product_types': {
        'category_name': ('product_categories', 'name', 'name'), # Filter by name
        'workshop_name': ('workshops', 'name', 'name'),         # Filter by name
    },
    'get_product_assembly_summary': {
        'p_start_date': 'date',
        'p_end_date': 'date',
        'agg_level': [
            'enterprise_total',
            'enterprise_by_category',
            'workshop_total',
            'workshop_by_category',
            'section_total',
            'section_by_category'
        ],
        'workshop': ('workshops', 'name', 'name'),
        'section': ('sections', 'name', 'name'),
        'category': ('product_categories', 'name', 'name'),
    },
    'v_staff_composition': {
        'worker_type_name': ('worker_types', 'name', 'name'),
        'is_master': 'boolean',
        'is_wsh_super': 'boolean',
        'workshop_name': ('workshops', 'name', 'name'),
        'section_name': ('sections', 'name', 'name'),
        'active_only': 'boolean', # Represents 'leave_date IS NULL'
    },
    'v_sections_and_chiefs_summary': {
        'workshop_id': ('workshops', 'name', 'wsh_id'),
    },
    'v_product_assembly_history': {
        'product_id': ('products', 'name', 'p_id'),
    },
    'v_brigade_composition': {
        'workshop_id': ('workshops', 'name', 'wsh_id'),
        'section_id': ('sections', 'name', 's_id'),
    },
    'v_section_masters': {
        'workshop_id': ('workshops', 'name', 'wsh_id'),
        'section_id': ('sections', 'name', 's_id'),
    },
    'v_currently_assembling': {
        'workshop_id': ('workshops', 'name', 'wsh_id'),
        'section_id': ('sections', 'name', 's_id'),
        'category_id': ('product_categories', 'name', 'c_id'),
    },
    'v_product_brigade_composition': {
        'product_id': ('products', 'name', 'p_id'),
        'brigade_id': ('brigade', 'name', 'b_id'),
    },
    'v_product_test_labs': {
        'product_id': ('products', 'name', 'p_id'),
        'lab_id': ('labs', 'name', 'l_id'),
    },
    'v_lab_tested_products': {
        'lab_id': ('labs', 'name', 'l_id'),
        'category_id': ('product_categories', 'name', 'c_id'),
        'start_date': 'date_range_start:test_date',
        'end_date': 'date_range_end:test_date',
    },
    'v_testers_activity': {
        'lab_id': ('labs', 'name', 'l_id'),
        'tester_w_id': ('employees', 'full_name', 'w_id'),
        'category_id': ('product_categories', 'name', 'c_id'),
        'start_date': 'date_range_start:test_date',
        'end_date': 'date_range_end:test_date',
    },
    'v_equipment_usage': {
        'lab_id': ('labs', 'name', 'l_id'),
        'equipment_id': ('equipment', 'name', 'e_id'),
        'category_id': ('product_categories', 'name', 'c_id'),
        'start_date': 'date_range_start:test_date',
        'end_date': 'date_range_end:test_date',
    },
    'v_ongoing_product_counts': {
        'workshop_name': ('workshops', 'name', 'name'),
        'section_name': ('sections', 'name', 'name'),
        'category_name': ('product_categories', 'name', 'name'),
    },
}
