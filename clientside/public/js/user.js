frappe.ui.form.on('User', {
	before_save: async function (frm) {
        // frappe.msgprint('st');
		const r = await fetch("/api/method/clientside.clientside.utils.getUsage");
        const { message } = await r.json();
        var getusr = await frappe.db.count('User', { filters: { enabled: 1 } });
        const url = new URL(window.location.href);
        
        // console.log(url.href.includes('new-user'))
        if (message.plan == "OneHash Starter") {
            if (getusr>=12 && url.href.includes('new-user')){
                frappe.throw("User Creation Limit Reached !")
                // frm.disable_save();
                // window.location.href = "https://abhichou-.onehash.is/app/user";
                
            }
            
          }
          if (message.plan == "OneHash Plus") {
            if (getusr>=32 && url.href.includes('new-user')){
                frappe.throw("User Creation Limit Reached !")
                // frm.disable_save();
                // window.location.href = "https://abhichou-.onehash.is/app/user";
                
            }
            
          }
	},
    onload: async function (frm) {
        // frappe.msgprint('st');
		const r = await fetch("/api/method/clientside.clientside.utils.getUsage");
        const { message } = await r.json();
        var getusr = await frappe.db.count('User', { filters: { enabled: 1 } });
        const url = new URL(window.location.href);
        // console.log(url.href.includes('new-user'))
        if (message.plan == "OneHash Starter") {
            if (getusr>=12 && url.href.includes('new-user')){
                // 
                frm.disable_save();
                frappe.throw("User Creation Limit Reached !")
                // window.location.href = "https://abhichou-.onehash.is/app/user";
                
            }
            
          }
          if (message.plan == "OneHash Plus") {
            if (getusr>=32 && url.href.includes('new-user')){
                // 
                frm.disable_save();
                frappe.throw("User Creation Limit Reached !")
                // window.location.href = "https://abhichou-.onehash.is/app/user";
                
            }
            
          }
	}
});