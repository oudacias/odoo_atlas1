odoo.define('petrol_station_doosys.screens', function (require) {
"use strict";
debugger
alert("hello world")

var screens = require('point_of_sale.screens');

var OrderWidget  = screens.OrderWidget.include({

  set_value: function(val) {
        debugger
    	var order = this.pos.get_order();
    	if (order.get_selected_orderline()) {
            var mode = this.numpad_state.get('mode');
            if( mode === 'quantity'){
                order.get_selected_orderline().set_quantity(val);
            }else if( mode === 'discount'){
                order.get_selected_orderline().set_discount(val);
            }else if( mode === 'price'){
                // ussef
                var selected_orderline = order.get_selected_orderline();
                var product =selected_orderline.product
                var q = val/product.list_price
                order.get_selected_orderline().set_quantity(q);

                //selected_orderline.price_manually_set = true;
                //selected_orderline.set_unit_price(val);
            }
    	}
    },


})



});