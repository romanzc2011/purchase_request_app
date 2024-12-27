import React from "react";

interface Purchase {
  BOC: number;
  fund: string;
  location: string;
  description: string;
  quantity: number;
  price: number;
  estimatedCost: number;
  justification: string;
}

interface PurchaseProps {
  purchases: Purchase[];
  onDelete: (BOC: number) => void;
}

const PurchaseList = ({ purchases, onDelete }: PurchaseProps) => {
  if (purchases.length === 0) return null;
  return (
    <div className="table-responsive rounded-3">
      <table className="table table-sm table-bordered">
        <thead className="custom-thead">
          <tr>
            <th>BOC</th>
            <th>Fund</th>
            <th>Location</th>
            <th>Description</th>
            <th>Quantity</th>
            <th>Price</th>
            <th>EstimatedCost</th>
            <th colSpan={2}>Justification</th>
            
          </tr>
        </thead>
        <tbody>
          {purchases.map((purchase) => (
            <tr key={purchase.BOC}>
              <td>{purchase.BOC}</td>
              <td>{purchase.fund}</td>
              <td>{purchase.location}</td>
              <td>{purchase.description}</td>
              <td>{purchase.quantity}</td>
              <td>{purchase.price}</td>
              <td>{purchase.estimatedCost}</td>
              <td>{purchase.justification}</td>
              <td>
                <button
                  className="btn btn-danger"
                  onClick={() => onDelete(purchase.BOC)}
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr>
            <td className="text-end" colSpan={8}>
              <strong>Purchase Total</strong>
            </td>
            <td colSpan={2}>
              $
              {purchases
                .reduce((acc, purchase) => purchase.estimatedCost + acc, 0)
                .toFixed(2)}
            </td>
          </tr>
        </tfoot>
      </table>
    </div>
  );
};

export default PurchaseList;
