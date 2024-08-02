const grid = document.querySelector('revo-grid');
// const plugin = { 'numeric': new NumberColumnType('0,0'), 'select': new SelectTypePlugin() };
const columnTemplate = (createElement, column) => {
    return createElement('span', {
      style: {
        color: 'blue'
      },
    }, createElement('div', {
        class: 'me'
    }, column.name));
};
const columnHTMLTemplate = (createElement, column) => {
  return createElement('div', {
        class: 'btn btn-default btn-xs btn-link-to-form',
        style: {
          'border': '1px solid #d1d8dd',
          'margin': '2px',
          'min-width': '50px',
          'text-align': 'left'

        },
    }, createElement('p', {
        style: {
          'text-align': 'left',
          'margin': '0px',
          'font-size': '11px'
        }
    }, column.name));
  };

const filterNames = {
    none: 'None',
    empty: 'Not set',
    notEmpty: 'Set',

    eq: 'Equal',
    notEq: 'Not equal',
    begins: 'Begins with',
    contains: 'Contains',
    notContains: 'Does not contain',

    eqN: '=',
    neqN: '!=',
    gt: '>',
    gte: '>=',
    lt: '<',
    lte: '<=',
};
const columns = [
  {
      prop: 'idx',
      name: 'ID',
      pin: 'colPinStart',
      autoSize: true,
       readonly: true,
      sortable: true,
  order: 'asc',
  // columnTemplate,
  //   cellTemplate: (createElement, props) => {
  //       return createElement('span',
  //       {
  //        class: "revo-draggable",
  //       },
  //       createElement('span', {
  //       class:"revo-drag-icon"
  //   }),props.model[props.prop]);
  //   }
  },
  {
      prop: 'attribute_html',
      name: 'Attribute',
      pin: 'colPinStart',
      autoSize: true,
      size:200,
      readonly: true,
      columnTemplate,
      cellTemplate: (createElement, props) => {
        // return $(`<div class="btn btn-default btn-xs btn-link-to-form" style="border: 1px solid #d1d8dd;margin: 2px;min-width: 50px;text-align: left;"><p style="text-align: left;margin: 0px;font-size: 11px;">Liter</p> <b>2L</b></div><div class="btn btn-default btn-xs btn-link-to-form" style="border: 1px solid #d1d8dd;margin: 2px;min-width: 50px;text-align: left;"><p style="text-align: left;margin: 0px;font-size: 11px;">Size</p> <b>Small</b></div><div class="btn btn-default btn-xs btn-link-to-form" style="border: 1px solid #d1d8dd;margin: 2px;min-width: 50px;text-align: left;"><p style="text-align: left;margin: 0px;font-size: 11px;">Color</p> <b>Grey</b></div>`);
      // return createElement('div',
      //   {
      //     style: { backgroundColor: 'red' },
      //     class: { 'inner-cell': true },
      //   },
      //   props.model[props.prop] || '',
      // );
      var htmldata = createElement('div', {

      },createElement('div', {
        class: 'btn btn-default btn-xs btn-link-to-form',
        style: {
          'border': '1px solid #d1d8dd',
          'margin': '2px',
          'min-width': '50px',
          'text-align': 'left'

        },
    }, createElement('p', {
        style: {
          'text-align': 'left',
          'margin': '0px',
          'font-size': '11px'
        }
    }, "Liter" || ''),createElement('b', {
        style: { }
    }, "2L")),createElement('div', {
        class: 'btn btn-default btn-xs btn-link-to-form',
        style: {
          'border': '1px solid #d1d8dd',
          'margin': '2px',
          'min-width': '50px',
          'text-align': 'left'

        },
    }, createElement('p', {
        style: {
          'text-align': 'left',
          'margin': '0px',
          'font-size': '11px'
        }
    }, "Color" || ''),createElement('b', {
        style: { }
    }, "Red")),createElement('div', {
        class: 'btn btn-default btn-xs btn-link-to-form',
        style: {
          'border': '1px solid #d1d8dd',
          'margin': '2px',
          'min-width': '50px',
          'text-align': 'left'

        },
    }, createElement('p', {
        style: {
          'text-align': 'left',
          'margin': '0px',
          'font-size': '11px'
        }
    }, "Size" || ''),createElement('b', {
        style: { }
    }, "Small")));
    
      return htmldata
    },
  },
  
  {
      prop: 'stock',
      name: 'Stock',
      columnType: 'numeric',
      autoSize: true,
        cellTemplate: (createElement, props) => {
          if(props.model[props.prop]>0){
        return createElement('span',
        {
         // class: "bubble",
         style: {"background-color": "green","color": "#fff","border": "none",
              "cursor": "default",
              "height": "32px",
              "display": "inline-flex",
              "outline": 0,
              "padding": "0 10px",
              "font-size": "0.8125rem",
              "box-sizing": "border-box",
              "transition": "background-color 300ms cubic-bezier(0.4, 0, 0.2, 1) 0ms,box-shadow 300ms cubic-bezier(0.4, 0, 0.2, 1) 0ms",
              "align-items": "center",
              "white-space": "nowrap",
              "border-radius": "16px",
              "vertical-align": "middle",
              "justify-content": "center",
              "text-decoration": "none",
              // "background-color": "#e0e0e0",
              "opacity": "0.7"}
           },props.model[props.prop]);
      }else{
         return createElement('span',
        {
         // class: "bubble",
         style: {"background-color": "red","color": "#fff","border": "none",
              "cursor": "default",
              "height": "32px",
              "display": "inline-flex",
              "outline": 0,
              "padding": "0 10px",
              "font-size": "0.8125rem",
              "box-sizing": "border-box",
              "transition": "background-color 300ms cubic-bezier(0.4, 0, 0.2, 1) 0ms,box-shadow 300ms cubic-bezier(0.4, 0, 0.2, 1) 0ms",
              "align-items": "center",
              "white-space": "nowrap",
              "border-radius": "16px",
              "vertical-align": "middle",
              "justify-content": "center",
              "text-decoration": "none",
              // "background-color": "#e0e0e0",
              "opacity": "0.7"}
           },"No Stock");
      }
    },
      aftersourceset: (props)=>{
        console.log("------props----")
      }
  },
  {
      prop: 'weight',
      name: 'Weight (In grams)',
      columnType: 'numeric',
      autoSize: true
     
  },
  {
      prop: 'sku',
      name: 'SKU',
      autoSize: true,
      cellTemplate: (createElement, props) => {
        return props.model[props.prop] || "-"
      }
    
  },
  {
      prop: 'price',
      name: 'Price',
      columnType: 'numeric',
      autoSize: true,
     columnTemplate,
    
  },
 {
      name: 'Role Based Pricing',
      children: [
          { name: 'Customer', prop: 'price',autoSize: true }, 
          { name: 'Reseller', prop: 'cust',autoSize: true,cellTemplate: (createElement, props) => {
        return props.model[props.prop] || 0
      }, }
      ]
  } ,
  {
      prop: 'attribute_id',
      name: 'Attribute ID',
      autoSize: true,
      pin: 'colPinEnd',
       readonly: true,
      columnTemplate
  }
];
const rows = cur_frm.doc.variant_combination;
grid.theme = 'compact';
grid.autoSizeColumn = true;
grid.columns = columns;
grid.source = rows;
grid.range= true;
// grid.rowHeaders = true;
// grid.columnTypes = plugin;
grid.rowSize = 50;

