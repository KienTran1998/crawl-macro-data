// ============================================================
// SCRAPER DỮ LIỆU HẢI QUAN VIỆT NAM
// ============================================================
// 
// HƯỚNG DẪN SỬ DỤNG:
// 1. Mở trang: https://www.customs.gov.vn/index.jsp?pageId=444&group=C%C3%B4ng%20b%E1%BB%91%20v
// 2. Mở Developer Console (F12 hoặc Cmd+Option+I)
// 3. Copy TOÀN BỘ code này vào Console và nhấn Enter
// 4. Chờ script chạy xong (khoảng 2-3 phút)
// 5. File JSON sẽ tự động download
// ============================================================

(async () => {
    console.log('🚀 Bắt đầu cào dữ liệu Hải quan Việt Nam...');
    console.log('⏳ Quá trình này sẽ mất khoảng 2-3 phút. Vui lòng chờ...\n');
    
    // Helper function để cào dữ liệu trang hiện tại
    const scrapePage = () => {
        const table = document.querySelector('table.list');
        if (!table) {
            console.warn('⚠️  Không tìm thấy bảng dữ liệu');
            return [];
        }
        
        const rows = Array.from(table.querySelectorAll('tr')).slice(1); // Bỏ header
        return rows.map(row => {
            const cells = Array.from(row.querySelectorAll('td')).map(td => td.innerText.trim());
            
            // Chỉ lấy dòng có số STT hợp lệ
            if (!cells[0] || isNaN(parseInt(cells[0]))) return null;
            
            return {
                stt: cells[0],
                chi_tieu: cells[1],
                dien_giai: cells[2],
                ky: cells[3],
                tri_gia_ty_usd: cells[4],
                tang_giam_ky_truoc_percent: cells[5],
                luy_ke_ty_usd: cells[6],
                tang_giam_cung_ky_percent: cells[7]
            };
        }).filter(r => r !== null);
    };

    // Helper function để chuyển trang
    const goToPage = async (pageNum) => {
        const select = document.querySelector('#slPages');
        if (!select) {
            console.error('❌ Không tìm thấy dropdown phân trang');
            return false;
        }
        
        const oldVal = select.value;
        const newVal = (pageNum - 1) * 20;
        select.value = newVal.toString();
        
        // Trigger change event
        if (select.onchange) select.onchange();
        
        // Đợi trang thay đổi
        let count = 0;
        while (document.querySelector('#slPages').value === oldVal && count < 50) {
            await new Promise(r => setTimeout(r, 100));
            count++;
        }
        
        // Đợi thêm để bảng load xong
        await new Promise(r => setTimeout(r, 300));
        return true;
    };

    // Bắt đầu scraping
    const allData = [];
    const select = document.querySelector('#slPages');
    
    if (!select) {
        console.error('❌ Không tìm thấy dropdown phân trang. Đảm bảo bạn đang ở đúng trang Hải quan!');
        return;
    }
    
    const totalPages = select.options.length;
    console.log(`📊 Tổng số trang cần cào: ${totalPages} trang\n`);
    
    // Tiến trình bar
    const startTime = Date.now();
    
    for (let page = 1; page <= totalPages; page++) {
        const success = await goToPage(page);
        if (!success) {
            console.error(`❌ Lỗi khi chuyển đến trang ${page}`);
            break;
        }
        
        const pageData = scrapePage();
        allData.push(...pageData);
        
        // Hiển thị tiến trình
        if (page % 10 === 0 || page === 1 || page === totalPages) {
            const percentage = ((page / totalPages) * 100).toFixed(1);
            const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
            console.log(`✓ Trang ${page}/${totalPages} (${percentage}%) | ${allData.length} records | ${elapsed}s`);
        }
    }
    
    // Hoàn thành
    const totalTime = ((Date.now() - startTime) / 1000).toFixed(1);
    console.log(`\n${'='.repeat(60)}`);
    console.log(`🎉 HOÀN THÀNH!`);
    console.log(`${'='.repeat(60)}`);
    console.log(`✓ Tổng số records: ${allData.length}`);
    console.log(`✓ Thời gian: ${totalTime}s`);
    console.log(`✓ Tốc độ: ${(totalPages / totalTime).toFixed(2)} trang/giây`);
    
    // Tạo và download file JSON
    const jsonStr = JSON.stringify(allData, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'customs_data.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    console.log(`\n💾 File JSON đã được download!`);
    console.log(`📝 Tên file: customs_data.json`);
    console.log(`📦 Dung lượng: ${(jsonStr.length / 1024).toFixed(2)} KB`);
    console.log(`\n📂 Di chuyển file vào: scrapers/customs_vn/data/customs_data.json`);
    
    // Hiển thị mẫu dữ liệu
    console.log(`\n${'='.repeat(60)}`);
    console.log(`MẪU DỮ LIỆU (3 dòng đầu):`);
    console.log(`${'='.repeat(60)}`);
    allData.slice(0, 3).forEach((row, i) => {
        console.log(`\nDòng ${i + 1}:`, row);
    });
    
    return allData.length;
})();
