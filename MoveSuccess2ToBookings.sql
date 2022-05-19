CREATE DEFINER=`fmadmin`@`%` PROCEDURE `MoveSuccess2ToBookings`()
BEGIN

-- Variables
DECLARE v_b_bookingID_Visual int(11);
DECLARE v_start_b_bookingID_Visual int(11);
DECLARE v_end_b_bookingID_Visual int(11);
DECLARE first_name char(64);
DECLARE last_name char(64);
DECLARE pk_id_dme_client int(11);
DECLARE booking_created_for_email char(255);
DECLARE bookingID_Visual int(11);
DECLARE api_booking_quote_id int(11);
DECLARE _running_flag tinyint;
DECLARE _start_time datetime(6);


DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
    GET DIAGNOSTICS CONDITION 1
    @p1 = RETURNED_SQLSTATE, @p2 = MESSAGE_TEXT;
    SELECT @p1 AS RETURNED_SQLSTATE, @p2 AS MESSAGE_TEXT;
        ROLLBACK;
        DROP TABLE IF EXISTS dme_memory;
    END;

SELECT is_running, start_time INTO _running_flag, _start_time FROM dme_options WHERE option_name = 'MoveSuccess2ToBookings';
SELECT _running_flag, _start_time;

IF NOT _running_flag OR (_running_flag AND _start_time < DATE_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 MINUTE)) THEN
    SELECT _running_flag, _start_time;
    -- LOCK
    UPDATE dme_options SET is_running = 1, start_time=CURRENT_TIMESTAMP() WHERE option_name = 'MoveSuccess2ToBookings';
    COMMIT;

    DROP TABLE IF EXISTS dme_memory;
    START TRANSACTION;

    SELECT max(b_bookingID_Visual) into v_b_bookingID_Visual FROM dme_bookings;

    If (v_b_bookingID_Visual is NULL ) THEN
        SET v_b_bookingID_Visual := 89600;
    END If;

    SELECT 'Starting with Visual Id ' + v_b_bookingID_Visual;

    SET v_start_b_bookingID_Visual = v_b_bookingID_Visual + 1;


    INSERT IGNORE INTO `dme_bookings` 
        (`pk_booking_id`, `b_clientReference_RA_Numbers`,
        `total_lines_qty_override`, `vx_freight_provider`, `v_vehicle_Type`, 
        `booking_Created_For`, `booking_Created_For_Email`, `x_ReadyStatus`, 
        `b_booking_Priority`, `b_handling_Instructions`, `pu_PickUp_Instructions_Contact`, 
        `pu_pickup_instructions_address`, `pu_WareHouse_Number`, `pu_WareHouse_Bay`, 
        `b_booking_tail_lift_pickup`, `b_booking_no_operator_pickup`, `puPickUpAvailFrom_Date`, 
        `pu_PickUp_Avail_Time_Hours`, `pu_PickUp_Avail_Time_Minutes`, `pu_PickUp_By_Date`, 
        `pu_PickUp_By_Time_Hours`, `pu_PickUp_By_Time_Minutes`, `pu_Address_Type`, 
        `pu_Address_Street_1`, `pu_Address_street_2`, `pu_Address_State`, 
        `pu_Address_Suburb`, `pu_Address_PostalCode`, `pu_Address_Country`, 
        `pu_Contact_F_L_Name`, `pu_email_Group`, `pu_Phone_Main`, 
        `pu_Comm_Booking_Communicate_Via`, `de_to_addressed_Saved`, `b_booking_tail_lift_deliver`, 
        `b_bookingNoOperatorDeliver`, `de_to_Pick_Up_Instructions_Contact`, `de_to_PickUp_Instructions_Address`, 
        `de_to_WareHouse_Bay`, `de_to_WareHouse_Number`, `de_Deliver_From_Date`, 
        `de_Deliver_From_Hours`, `de_Deliver_From_Minutes`, `de_Deliver_By_Date`, 
        `de_Deliver_By_Hours`, `de_Deliver_By_Minutes`, `de_To_AddressType`, 
        `deToCompanyName`, `de_To_Address_Street_1`, `de_To_Address_Street_2`, 
        `de_To_Address_State`, `de_To_Address_Suburb`, `de_To_Address_PostalCode`, 
        `de_To_Address_Country`, `de_to_Contact_F_LName`, `de_Email_Group_Emails`, 
        `de_to_Phone_Main`, `de_to_Phone_Mobile`, `de_To_Comm_Delivery_Communicate_Via`, 
        `total_1_KG_weight_override`, `zb_002_client_booking_key`, `z_CreatedTimestamp`, 
        `b_bookingID_Visual`, `fk_client_warehouse_id`, `kf_client_id`, 
        `vx_serviceName`, `b_booking_Category`, `b_booking_Notes`, 
        `puCompany`, `pu_Email`, `pu_Phone_Mobile`, 
        `de_Email`, `v_service_Type`, `v_FPBookingNumber`,
        `b_status`, 
        `b_status_category`,
        `b_client_booking_ref_num`, `b_client_del_note_num`,
        `b_client_order_num`, `b_client_sales_inv_num`, `b_client_warehouse_code`,
        `b_client_name`, `delivery_kpi_days`, `z_api_issue_update_flag_500`,
        `x_manual_booked_flag`, `x_booking_Created_With`, `api_booking_quote_id`,
        `booking_type`, `vx_fp_order_id`, `b_clientPU_Warehouse`,
        `b_promo_code`)
    SELECT bok_1.pk_header_id, bok_1.b_000_1_b_clientReference_RA_Numbers,
        bok_1.b_000_b_total_lines, bok_1.b_001_b_freight_provider, b_002_b_vehicle_type,
        bok_1.b_005_b_created_for, bok_1.b_006_b_created_for_email, b_007_b_ready_status,
        bok_1.b_009_b_priority, bok_1.b_014_b_pu_handling_instructions, b_015_b_pu_instructions_contact,
        bok_1.b_016_b_pu_instructions_address, bok_1.b_017_b_pu_warehouse_num, b_018_b_pu_warehouse_bay,
        bok_1.b_019_b_pu_tail_lift, bok_1.b_020_b_pu_num_operators, b_021_b_pu_avail_from_date,
        bok_1.b_022_b_pu_avail_from_time_hour, bok_1.b_023_b_pu_avail_from_time_minute, b_024_b_pu_by_date,
        bok_1.b_025_b_pu_by_time_hour, bok_1.b_026_b_pu_by_time_minute, b_027_b_pu_address_type,
        bok_1.b_029_b_pu_address_street_1, bok_1.b_030_b_pu_address_street_2, b_031_b_pu_address_state,
        bok_1.b_032_b_pu_address_suburb, bok_1.b_033_b_pu_address_postalcode, b_034_b_pu_address_country,
        bok_1.b_035_b_pu_contact_full_name, bok_1.b_036_b_pu_email_group, b_038_b_pu_phone_main,
        bok_1.b_040_b_pu_communicate_via, bok_1.pu_addressed_saved, b_041_b_del_tail_lift,
        bok_1.b_042_b_del_num_operators, b_043_b_del_instructions_contact, b_044_b_del_instructions_address,
        bok_1.b_045_b_del_warehouse_bay, b_046_b_del_warehouse_number, b_047_b_del_avail_from_date,
        bok_1.b_048_b_del_avail_from_time_hour, b_049_b_del_avail_from_time_minute, b_050_b_del_by_date,
        bok_1.b_051_b_del_by_time_hour, b_052_b_del_by_time_minute, b_053_b_del_address_type,
        bok_1.b_054_b_del_company, b_055_b_del_address_street_1, b_056_b_del_address_street_2,
        bok_1.b_057_b_del_address_state, b_058_b_del_address_suburb, b_059_b_del_address_postalcode,
        bok_1.b_060_b_del_address_country, b_061_b_del_contact_full_name, b_062_b_del_email_group,
        bok_1.b_064_b_del_phone_main, b_065_b_del_phone_mobile, b_066_b_del_communicate_via,
        bok_1.total_kg, v_client_pk_consigment_num, bok_1.z_createdTimeStamp,
        @a:=@a+1, bok_1.fk_client_warehouse_id, fk_client_id,
        bok_1.b_003_b_service_name, b_008_b_category, b_010_b_notes,
        bok_1.b_028_b_pu_company, b_037_b_pu_email, b_039_b_pu_phone_mobile,
        bok_1.b_063_b_del_email, vx_serviceType_XXX, bok_1.b_000_3_consignment_number,
        CASE 
            WHEN success = 2
                AND (bok_1.b_000_3_consignment_number IS NOT NULL AND bok_1.b_000_3_consignment_number <> "")
                THEN 'Booked'
            WHEN success = 2
                AND (bok_1.b_000_3_consignment_number IS NULL OR bok_1.b_000_3_consignment_number = "") 
                THEN 'Ready for booking'
            WHEN success = 4
                THEN 'Picking'
            WHEN success = 5
                THEN 'Imported / Integrated'
        END,
        CASE 
            WHEN success = 2
                AND (bok_1.b_000_3_consignment_number IS NOT NULL AND bok_1.b_000_3_consignment_number <> "")
                THEN 'Booked'
            WHEN success = 2
                AND (bok_1.b_000_3_consignment_number IS NULL OR bok_1.b_000_3_consignment_number = "") 
                THEN 'Pre Booking'
            WHEN success = 4
                THEN 'Pre Booking'
            WHEN success = 5
                THEN 'Pre Booking'
        END,
        bok_1.client_booking_id, b_client_del_note_num,
        b_client_order_num, b_client_sales_inv_num, b_client_warehouse_code,
        dme_clients.company_name , IFNULL(delivery_days, 14),
        CASE WHEN success = 2 THEN 1 WHEN success = 3 THEN 0 WHEN success= 4 THEN 0 END,
        CASE WHEN success = 6 THEN 1 ELSE 0 END,
        bok_1.x_booking_Created_With, bok_1.quote_id,
        bok_1.b_092_booking_type, '', bok_1.b_clientPU_Warehouse,
        bok_1.b_093_b_promo_code
    FROM bok_1_headers bok_1
    LEFT OUTER JOIN dme_clients ON fk_client_id=dme_account_num
    LEFT OUTER JOIN utl_fp_delivery_times ON (b_001_b_freight_provider = fp_name AND cast(b_059_b_del_address_postalcode AS UNSIGNED) 
    BETWEEN postal_code_from AND postal_code_to), (SELECT @a:= v_b_bookingID_Visual) AS a 
    WHERE success IN (2, 4, 5);

    SET v_end_b_bookingID_Visual = v_start_b_bookingID_Visual + (ROW_COUNT() - 1);

    SELECT 'Rows moved to dme_bookings = ' + ROW_COUNT();

    CREATE TABLE dme_memory (id INT, kf_client_id VARCHAR(64), b_client_sales_inv_num VARCHAR(64), b_bookingID_Visual_List varchar(100));

    insert InTo dme_memory (id, kf_client_id, b_client_sales_inv_num, b_bookingID_Visual_List)
    select max(id), kf_client_id, b_client_sales_inv_num, Group_Concat(b_bookingID_Visual SEPARATOR ', ')
    from (
    select id, kf_client_id, b_client_sales_inv_num, b_bookingID_Visual
    from dme_bookings where b_bookingID_Visual < v_start_b_bookingID_Visual
    and b_status not in ('Cancelled', 'Closed') 
    and kf_client_id is not null and b_client_sales_inv_num is not null and length(b_client_sales_inv_num) > 0
    and (kf_client_id, b_client_sales_inv_num) in (select kf_client_id, b_client_sales_inv_num from dme_bookings
                                                    where b_bookingID_Visual between v_start_b_bookingID_Visual and v_end_b_bookingID_Visual
                                                    )
    union
    select id, kf_client_id, b_client_sales_inv_num, b_bookingID_Visual from dme_bookings
    where b_bookingID_Visual between v_start_b_bookingID_Visual and v_end_b_bookingID_Visual
    and kf_client_id is not null and b_client_sales_inv_num is not null and length(b_client_sales_inv_num) > 0
    ) t
    group by kf_client_id, b_client_sales_inv_num
    having count(*) > 1;

    Update dme_bookings join dme_memory on dme_bookings.id=dme_memory.id
    SET dme_bookings.b_error_Capture = Concat('SINV is duplicated in bookingID = ' , dme_memory.b_bookingID_Visual_List), dme_bookings.b_status = 'On Hold';

    DROP TABLE dme_memory;

    UPDATE bok_1_headers SET success=1 WHERE success IN (2, 4, 5);


    SELECT 'Starting move of booking lines';

    INSERT IGNORE INTO dme_booking_lines
        (e_spec_clientRMA_Number, e_weightPerEach,
        e_1_Total_dimCubicMeter, total_2_cubic_mass_factor_calc, e_Total_KG_weight,
        e_item, e_qty, e_type_of_packaging,
        e_item_type, e_pallet_Type, fk_booking_id,
        e_dimLength, e_dimWidth, e_dimHeight,
        e_weightUOM, z_createdTimeStamp, e_dimUOM,
        client_item_reference, pk_booking_lines_id, zbl_121_integer_1,
        zbl_102_text_2, is_deleted, packed_status)
    SELECT client_booking_id, l_009_weight_per_each,
        CASE
            WHEN upper(l_004_dim_UOM) = "CM"
                THEN l_002_qty * (l_005_dim_length * l_006_dim_width * l_007_dim_height / 1000000)
            WHEN upper( l_004_dim_UOM) IN ( "METER", "M")
                THEN (l_002_qty * l_005_dim_length * l_006_dim_width * l_007_dim_height)
            ELSE l_002_qty * (l_005_dim_length * l_006_dim_width * l_007_dim_height / 1000000000)
        END,
        CASE
            WHEN upper(l_004_dim_UOM) = "CM"
                THEN l_002_qty * (l_005_dim_length * l_006_dim_width * l_007_dim_height / 1000000) * 250
            WHEN upper( l_004_dim_UOM) IN ( "METER", "M")
                THEN (l_002_qty * l_005_dim_length * l_006_dim_width * l_007_dim_height) * 250
            ELSE l_002_qty * (l_005_dim_length * l_006_dim_width * l_007_dim_height / 1000000000) * 250
        END,
        CASE 
            WHEN lower(l_008_weight_UOM) IN ("g", "gram", "grams")
                THEN l_002_qty * l_009_weight_per_each / 1000
            WHEN lower(l_008_weight_UOM) IN ("kilogram", "kilograms", "kg", "kgs")
                THEN l_002_qty * l_009_weight_per_each 
            WHEN lower(l_008_weight_UOM) IN ("t", "ton", "tons")
                THEN l_002_qty * l_009_weight_per_each * 1000
            Else
                0
        END,
        l_003_item, l_002_qty, l_001_type_of_packaging,
        e_item_type, e_pallet_type, v_client_pk_consigment_num,
        l_005_dim_length, l_006_dim_width, l_007_dim_height,
        l_008_weight_UOM, z_createdTimeStamp, l_004_dim_UOM,
        client_item_reference, pk_booking_lines_id, zbl_121_integer_1,
        zbl_102_text_2, 0, b_093_packed_status
    FROM `bok_2_lines`
    WHERE success IN (2, 4, 5);

    SELECT 'Rows moved to dme_booking_lines = ' + ROW_COUNT();

    UPDATE bok_2_lines SET success=1 WHERE success IN (2, 4, 5);


    SELECT 'Starting move of booking lines data';

    INSERT IGNORE INTO dme_booking_lines_data 
        (fk_booking_id, quantity,
        modelNumber, itemDescription, itemFaultDescription,
        itemSerialNumbers, insuranceValueEach, gap_ra,
        clientRefNumber, z_createdByAccount, z_createdTimeStamp,
        z_modifiedByAccount, z_modifiedTimeStamp, fk_booking_lines_id)
    SELECT v_client_pk_consigment_num, ld_001_qty,
        ld_002_model_number, ld_003_item_description, ld_004_fault_description,
        ld_005_item_serial_number, ld_006_insurance_value, ld_007_gap_ra,
        ld_008_client_ref_number, z_createdByAccount, z_createdTimeStamp,
        z_modifiedByAccount, z_modifiedTimeStamp, fk_booking_lines_id
    FROM `bok_3_lines_data`
    WHERE success IN (2, 4, 5);

    SELECT 'Rows moved to dme_booking_lines_data = ' + ROW_COUNT();

    UPDATE bok_3_lines_data SET success=1 WHERE success IN (2, 4, 5);


    SET bookingID_Visual = v_start_b_bookingID_Visual;
    bookingCreatedEmail: REPEAT 
        SELECT 
            SUBSTRING_INDEX(SUBSTRING_INDEX(dme_bookings.booking_Created_For, ' ', 1), ' ', -1),
            TRIM(SUBSTR(dme_bookings.booking_Created_For, LOCATE(' ', dme_bookings.booking_Created_For))),
            dme_bookings.api_booking_quote_id, dme_clients.pk_id_dme_client
        INTO first_name, last_name, api_booking_quote_id, pk_id_dme_client
        FROM dme_bookings 
        INNER JOIN dme_clients 
        ON dme_bookings.b_client_name=dme_clients.company_name AND dme_bookings.kf_client_id=dme_clients.dme_account_num
        WHERE dme_bookings.b_bookingID_Visual = bookingID_Visual;

        -- Populate 'booking_created_for'
        SELECT first_name, last_name, api_booking_quote_id, pk_id_dme_client;

        If first_name = "Bathroom"
            THEN
                UPDATE dme_bookings
                SET booking_Created_For_Email = "info@bathroomsalesdirect.com.au"
                WHERE b_bookingID_Visual = bookingID_Visual;
            ELSE
                If last_name = ""
                    THEN
                        -- SELECT 'Only first_name';
                        SELECT email INTO booking_created_for_email
                        FROM dme_client_employees
                        WHERE name_last IS NULL AND name_first=first_name AND fk_id_dme_client_id=pk_id_dme_client;
                    ELSE
                        -- SELECT 'first_name, last_name';
                        SELECT email INTO booking_created_for_email
                        FROM dme_client_employees
                        WHERE name_first=last_name AND name_last=first_name AND fk_id_dme_client_id=pk_id_dme_client;
                END If;

                SELECT booking_created_for_email;

                UPDATE dme_bookings
                SET booking_Created_For_Email = booking_created_for_email
                WHERE b_bookingID_Visual = bookingID_Visual;
        END If;

        -- Populate 'Quoted Cost' and 'Quoted $'
        If api_booking_quote_id THEN
            UPDATE dme_bookings booking
            INNER JOIN api_booking_quotes quote ON booking.api_booking_quote_id = quote.id
            SET booking.inv_sell_quoted = quote.client_mu_1_minimum_values, booking.inv_cost_quoted = quote.fee * (1 + quote.mu_percentage_fuel_levy)
            WHERE booking.b_bookingID_Visual = bookingID_Visual;
        END If;
        
        SET bookingID_Visual = bookingID_Visual + 1;
    UNTIL bookingID_Visual > v_end_b_bookingID_Visual
    END REPEAT bookingCreatedEmail;

    -- UNLOCK
    UPDATE dme_options SET is_running = 0, end_time=CURRENT_TIMESTAMP() WHERE option_name = 'MoveSuccess2ToBookings';
    COMMIT;
ELSE
    SELECT 'Procedure MoveSuccess2ToBookings is already running.';
END IF;

END
